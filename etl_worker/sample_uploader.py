"""
Script: sample_uploader.py
Purpose:
    Uploads all PDF files from a local folder to AWS S3 and sends SQS messages
    with the uploaded file keys for downstream ETL processing.
"""

import os
from aws_helper import AWSHelper
from pathlib import Path

def upload_pdfs_to_s3(pdf_folder: Path, aws_helper: AWSHelper, destination_folder: str = "input"):
    """
    Upload all PDF files in a folder to S3 and send SQS messages.

    Args:
        pdf_folder (Path): Local folder containing PDF files.
        aws_helper (AWSHelper): Initialized AWSHelper instance.
        destination_folder (str, optional): S3 folder to upload PDFs to. Defaults to "input".

    Raises:
        FileNotFoundError: If the provided pdf_folder does not exist.
    """
    if not pdf_folder.exists():
        raise FileNotFoundError(f"{pdf_folder} not found")

    for pdf_file in pdf_folder.glob("*.pdf"):
        print(f"Processing {pdf_file.name}...")

        # Upload PDF to S3
        uploaded = aws_helper.upload_file(str(pdf_file), pdf_file.name, destination_folder=destination_folder)
        if uploaded:
            print(f"Uploaded {pdf_file.name} to S3")

            # Send SQS message with the file key
            try:
                response = aws_helper.sqs.send_message(
                    QueueUrl=aws_helper.queue_url,
                    MessageBody=pdf_file.name
                )
                print(f"SQS message sent for {pdf_file.name}: {response.get('MessageId')}")
            except Exception as e:
                print(f"Failed to send SQS message for {pdf_file.name}: {e}")
        else:
            print(f"Failed to upload {pdf_file.name}")


if __name__ == "__main__":
    # Get PDFs folder from environment variable or use default
    pdf_folder_path = os.getenv("PDF_FOLDER_PATH", "./sample_pdfs")
    pdf_folder = Path(pdf_folder_path)

    # Initialize AWS helper
    aws = AWSHelper()

    # Upload PDFs and send SQS messages
    upload_pdfs_to_s3(pdf_folder, aws)
