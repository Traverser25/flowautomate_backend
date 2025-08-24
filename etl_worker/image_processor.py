# ocr_updater.py
import json
import logging
from pathlib import Path
from PIL import Image
import pytesseract
from datetime import datetime

# ---------------- Logging ----------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ---------------- Config ----------------
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
IMAGE_DIR = Path(r"C:\Users\HP\Desktop\flowautmate_assesment\parsed_pdf\images") #my  local  tesseract  replace witrh urs  

class OCRUpdater:
    """
    Processes images in a folder using Tesseract OCR and updates corresponding JSON files.

    Responsibilities:
        - Reads each PNG image in the directory.
        - Runs OCR to extract text.
        - Appends page and image information to the text.
        - Updates JSON files with OCR text and timestamp.
    """
    def __init__(self, image_dir: Path):
        self.image_dir = image_dir
        if not self.image_dir.exists():
            logger.error(f"Image directory '{self.image_dir}' does not exist.")
        else:
            logger.info(f"OCRUpdater initialized for directory: {self.image_dir}")

   
    def process_image(self, img_file: Path):
            try:
                json_file = img_file.with_suffix(".json")
                if not json_file.exists():
                    logger.warning(f"JSON not found for {img_file.name}, skipping...")
                    return

                # Load JSON first to get page_number and image_index
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # Run OCR
                img = Image.open(img_file)
                text = pytesseract.image_to_string(img).strip()

                # Append page and image info
                page_num = data.get("page_number", "unknown")
                img_index = data.get("image_index", "unknown")
                text += f"\n\nThis image belongs to page {page_num} and image num {img_index}."

                # Update JSON fields
                data["chunk_text"] = text
                data["ocr_processed_at"] = datetime.now().isoformat()

                # Save JSON
                with open(json_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)

                logger.info(f"OCR updated for {json_file.name}")
            except Exception as e:
                logger.error(f"Failed to process {img_file.name}: {e}", exc_info=True)


    def run(self):
        logger.info(f"Processing images in directory: {self.image_dir}")
        for img_file in self.image_dir.glob("*.png"):
            self.process_image(img_file)
        logger.info("All images processed and JSON updated.")

# ---------------- Exported function ----------------
# def update_json_with_ocr(image_dir: Path = IMAGE_DIR):
#     updater = OCRUpdater(image_dir)
#     updater.run()

# # ---------------- Main ----------------
# if __name__ == "__main__":
#     update_json_with_ocr()
