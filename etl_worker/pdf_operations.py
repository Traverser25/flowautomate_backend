# pdf_etl.py
import json
import logging
from pathlib import Path
from datetime import datetime
from PyPDF2 import PdfReader
import fitz  # PyMuPDF
import camelot
from langchain.text_splitter import RecursiveCharacterTextSplitter

# ---------------- Logging ----------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ---------------- Config ----------------
BASE_DIR = Path("parsed_pdf")
PARA_DIR = BASE_DIR / "paragraphs"
TABLE_DIR = BASE_DIR / "tables"
IMAGE_DIR = BASE_DIR / "images"



MAX_PAGES = 30  # for testing  ...avoid larger  pages for  local now 

# ---------------- LangChain Splitter ----------------
splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50,
    separators=["\n\n", "\n", " ", ""]
)

class PDFExtractor:
    """
    Handles extraction of structured content from PDF files.

    Supports:
        - Paragraph extraction using PyPDF2 and LangChain text splitter
        - Table extraction using Camelot
        - Image extraction using PyMuPDF (fitz)
    
    Extracted content is stored in JSON files in dedicated directories.
    """
    def __init__(self, pdf_path: str):
        self.pdf_path = Path(pdf_path)
        self.pdf_name = self.pdf_path.stem
        logger.info(f"Initialized PDFExtractor for '{self.pdf_name}'")
        for d in [PARA_DIR, TABLE_DIR, IMAGE_DIR]:
            d.mkdir(exist_ok=True, parents=True)

    def extract_paragraphs(self):

        """
        Extracts paragraphs from the PDF and saves them as JSON files.

        Uses LangChain RecursiveCharacterTextSplitter to split text into chunks.
        Each chunk is stored with metadata including page number, chunk type, and timestamp.
        """
        try:
            reader = PdfReader(str(self.pdf_path))
            logger.info("Extracting paragraphs...")
            for i, page in enumerate(reader.pages, start=1):
                if i > MAX_PAGES:
                    break
                text = page.extract_text()
                if not text:
                    continue
                chunks = splitter.split_text(text)
                paragraphs = []
                for j, chunk in enumerate(chunks, start=1):
                    record = {
                        "_id": f"{self.pdf_name}#page{i}#para{j}",
                        "chunk_text": chunk,
                        "doc_id": self.pdf_name,
                        "page_number": i,
                        "chunk_type": "paragraph",
                        "chunk_number": j,
                        "source": str(self.pdf_path),
                        "created_at": datetime.now().isoformat()
                    }
                    paragraphs.append(record)

                filename = f"{self.pdf_name}_page{i}_paragraphs.json"
                with open(PARA_DIR / filename, "w", encoding="utf-8") as f:
                    json.dump(paragraphs, f, indent=2)
            logger.info("Paragraphs extraction done.")
        except Exception as e:
            logger.error(f"Failed to extract paragraphs: {e}", exc_info=True)

    def extract_tables(self):
        try:
            logger.info("Extracting tables...")
            tables = camelot.read_pdf(str(self.pdf_path), pages=f'1-{MAX_PAGES}', flavor='stream')
            for i, table in enumerate(tables, start=1):
                table_csv = table.df.to_csv(index=False)
                chunks = splitter.split_text(table_csv)
                table_chunks = []
                for j, chunk in enumerate(chunks, start=1):
                    record = {
                        "_id": f"{self.pdf_name}#page{table.page}#table{i}#chunk{j}",
                        "chunk_text": chunk,
                        "doc_id": self.pdf_name,
                        "page_number": table.page,
                        "chunk_type": "table",
                        "chunk_number": j,
                        "table_index": i,
                        "source": str(self.pdf_path),
                        "created_at": datetime.now().isoformat()
                    }
                    table_chunks.append(record)

                filename = f"{self.pdf_name}_page{table.page}_table{i}.json"
                with open(TABLE_DIR / filename, "w", encoding="utf-8") as f:
                    json.dump(table_chunks, f, indent=2)
            logger.info("Tables extraction done.")
        except Exception as e:
            logger.warning(f"No tables extracted: {e}", exc_info=True)

    def extract_images(self):
        """
        Extracts images from the PDF and saves them as PNG files and JSON metadata.

        Uses PyMuPDF (fitz) to extract images per page.
        JSON metadata includes page number, image index, source, and placeholders for OCR text.
        """
        

        try:
            logger.info("Extracting images...")
            doc = fitz.open(self.pdf_path)
            for page_num in range(min(len(doc), MAX_PAGES)):
                page = doc[page_num]
                for img_index, img in enumerate(page.get_images(full=True)):
                    xref = img[0]
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    img_path = IMAGE_DIR / f"{self.pdf_name}_page{page_num+1}_img{img_index+1}.png"
                    with open(img_path, "wb") as f:
                        f.write(image_bytes)

                    # JSON metadata for the image (OCR will populate chunk_text later)
                    record = {
                        "_id": f"{self.pdf_name}#page{page_num+1}#img{img_index+1}",
                        "chunk_text": "",
                        "doc_id": self.pdf_name,
                        "page_number": page_num+1,
                        "chunk_type": "image",
                        "image_index": img_index+1,
                        "file_path": str(img_path),
                        "source": str(self.pdf_path),
                        "created_at": datetime.now().isoformat()
                    }

                    json_file = IMAGE_DIR / f"{self.pdf_name}_page{page_num+1}_img{img_index+1}.json"
                    with open(json_file, "w", encoding="utf-8") as jf:
                        json.dump(record, jf, indent=2)
            logger.info("Images extraction done.")
        except Exception as e:
            logger.error(f"Failed to extract images: {e}", exc_info=True)

# ---------------- Exported Function ----------------
def process_pdf(pdf_path: str):
    extractor = PDFExtractor(pdf_path)
    extractor.extract_paragraphs()
    extractor.extract_tables()
    extractor.extract_images()
