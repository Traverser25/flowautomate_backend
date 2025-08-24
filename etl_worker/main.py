import os
import time
import logging
from pathlib import Path
from colorama import init, Fore, Style
from aws_helper import AWSHelper
from pdf_operations import PDFExtractor
from image_processor import OCRUpdater
from pinecone_worker import PineconeWorker
from logger import MongoDBLogger
import shutil

# Initialize colorama
init(autoreset=True)

# Create PineconeWorker instance
pinecone_worker = PineconeWorker()
#pinecone_worker.delete_index()
#print(pinecone_worker.describe_index())

class ETLWorker:


    """
    ETLWorker handles the automated processing of PDFs uploaded to AWS S3.

    It polls an SQS queue, downloads PDF files, extracts content (paragraphs, tables, images),
    runs OCR on images, upserts structured data into Pinecone, and moves processed files
    while maintaining logs in both console and MongoDB.

    Attributes:
        project_root (Path): Root directory of the project.
        download_dir (Path): Directory where PDFs are downloaded.
        aws (AWSHelper): AWS helper instance for S3 and SQS operations.
        poll_interval (int): Time in seconds to wait between polling SQS.
        logger (logging.Logger): Logger for console and MongoDB logging.

    """
    def __init__(self, project_root: Path = None, poll_interval: int = 30, mongo_collection="etl_logs"):
        self.project_root = project_root or Path(__file__).parent
        self.download_dir = self.project_root / "downloads"
        self.download_dir.mkdir(exist_ok=True, parents=True)

        self.aws = AWSHelper()
        self.poll_interval = poll_interval

        # Logging setup
        self.logger = logging.getLogger("ETLWorker")
        self.logger.setLevel(logging.INFO)

        ch = logging.StreamHandler()
        ch.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
        self.logger.addHandler(ch)

        mongo_handler = MongoDBLogger(mongo_collection)
        mongo_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
        self.logger.addHandler(mongo_handler)

        self.logger.info(f"{Fore.GREEN}ETLWorker initialized. Download folder: {self.download_dir}{Style.RESET_ALL}")

    def process_sqs_messages(self):


        """
        Continuously polls the SQS queue for new PDF messages and processes them.

        For each message:
            1. Downloads the PDF from S3.
            2. Extracts paragraphs, tables, and images using PDFExtractor.
            3. Runs OCR on images using OCRUpdater.
            4. Upserts extracted JSON content into Pinecone namespaces (paragraphs, tables, images).
            5. Moves processed files to a "processed" folder in S3.
            6. Deletes the processed message from the SQS queue.
            7. Cleans up local temporary directories.

        Logs all activities and errors to both console and MongoDB.
        """
        while True:
            messages = self.aws.receive_messages()
            if not messages:
                print(f"{Fore.YELLOW}No messages in SQS queue. Waiting...{Style.RESET_ALL}")
                time.sleep(self.poll_interval)
                continue

            for msg in messages:
                try:
                    file_key = msg['Body']
                    local_path = self.download_dir / Path(file_key).name

                    if self.aws.download_file(file_key, str(local_path)):
                        print(f"{Fore.CYAN}Downloaded file: {file_key} -> {local_path}{Style.RESET_ALL}")
                        self.logger.info(f"Downloaded file: {file_key} -> {local_path}")

                        pdf_extractor = PDFExtractor(local_path)
                        pdf_extractor.extract_paragraphs()
                        pdf_extractor.extract_tables()
                        pdf_extractor.extract_images()
                        print(f"{Fore.MAGENTA}PDF extraction done for {local_path.name}{Style.RESET_ALL}")
                        self.logger.info(f"PDF extraction done for {local_path.name}")

                   


                        BASE_DIR = Path("parsed_pdf")
                        IMAGE_DIR = BASE_DIR / "images"
                        ocr = OCRUpdater(IMAGE_DIR)
                        ocr.run()
                        print(f"{Fore.BLUE}OCR completed for images of {pdf_extractor.pdf_name}{Style.RESET_ALL}")
                        self.logger.info(f"OCR completed for images of {pdf_extractor.pdf_name}")

                        # Upsert JSON folders into Pinecone
                        pinecone_worker.upsert_json_folder(BASE_DIR / "paragraphs", "pdf-paragraphs")
                        pinecone_worker.upsert_json_folder(BASE_DIR/ "tables", "pdf-tables")
                        pinecone_worker.upsert_json_folder(BASE_DIR / "images", "pdf-images")
                        print(f"{Fore.GREEN}Pinecone upsert done for {pdf_extractor.pdf_name}{Style.RESET_ALL}")
                        self.logger.info(f"Pinecone upsert done for {pdf_extractor.pdf_name}")

                        self.aws.move_file(file_key, "input", "processed")
                        print(f"{Fore.CYAN}Moved {file_key} to processed folder{Style.RESET_ALL}")
                        self.logger.info(f"Moved {file_key} to processed folder")

                    self.aws.delete_message(msg['ReceiptHandle'])
                    if BASE_DIR.exists():
                        shutil.rmtree(BASE_DIR)
                        print(f"{Fore.YELLOW}Deleted local folder: {BASE_DIR}{Style.RESET_ALL}")
                        self.logger.info(f"Deleted local folder: {BASE_DIR}")
                    break

                except Exception as e:
                    print(f"{Fore.RED}Failed to process message: {msg.get('Body', '')}, Error: {e}{Style.RESET_ALL}")
                    self.logger.error(f"Failed to process message: {msg.get('Body', '')}, Error: {e}", exc_info=True)

            time.sleep(self.poll_interval)


if __name__ == "__main__":
    etl = ETLWorker(poll_interval=10, mongo_collection="etl_logs")
    etl.process_sqs_messages()
