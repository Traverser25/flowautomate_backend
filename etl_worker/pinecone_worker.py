# pinecone_worker.py
import os
import json
import logging
from pathlib import Path
from pinecone import Pinecone

# ---------------- Logging ----------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ---------------- Config ----------------
PARA_DIR = Path("parsed_pdf/paragraphs")
TABLE_DIR = Path("parsed_pdf/tables")
IMAGE_DIR = Path("parsed_pdf/images")

class PineconeWorker:


    """
    Handles interaction with Pinecone for upserting and managing embeddings.

    Responsibilities:
        - Create/connect to a Pinecone index.
        - Upsert JSON content from folders into namespaces.
        - Describe index statistics.
        - Delete the Pinecone index if needed.

    Attributes:
        index_name (str): Name of the Pinecone index.
        pc (Pinecone): Pinecone client instance.
        index: Connected Pinecone index object.
    """
    def __init__(self, index_name: str = "automateflow"):
        self.index_name = index_name
        api_key = os.getenv("PINECONE_API_KEY")
        if not api_key:
            raise ValueError("PINECONE_API_KEY environment variable not set")

        # Initialize Pinecone client
        self.pc = Pinecone(api_key=api_key)

        # Delete index (optional)
        # self.pc.delete_index(self.index_name)

        # Create index if it doesn't exist
        if not self.pc.has_index(self.index_name):
            logger.info(f"Creating Pinecone index '{self.index_name}'...")
            self.pc.create_index_for_model(
                name=self.index_name,
                cloud="aws",
                region="us-east-1",
                embed={"model": "llama-text-embed-v2", "field_map": {"text": "chunk_text"}}
            )

        # Connect to the index
        self.index = self.pc.Index(self.index_name)
        logger.info(f"Connected to Pinecone index '{self.index_name}'")

    def upsert_json_folder(self, folder_path: Path, namespace: str):
        """Upserts JSON files from a folder into a Pinecone namespace."""



        """
        Upserts JSON files from a folder into a Pinecone namespace.

        Args:
            folder_path (Path): Path to the folder containing JSON files.
            namespace (str): Pinecone namespace to upsert the records into.

        Notes:
            - JSON can be a single dictionary or a list of dictionaries.
            - Images with empty text are skipped (OCR can populate text later).
        """
        try:
            files = list(folder_path.glob("*.json"))
            logger.info(f"Pushing {len(files)} files from '{folder_path}' into namespace '{namespace}'...")

            for file in files:
                with open(file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                if isinstance(data, dict):
                    data = [data]

                records = []
                for entry in data:
                    text = entry.get("chunk_text", "")
                    if not text and entry.get("chunk_type") != "image":
                        continue

                    record = {"_id": entry["_id"], "chunk_text": text}
                    # Merge in metadata
                    metadata = {k: v for k, v in entry.items() if k not in ["_id", "chunk_text"]}
                    record.update(metadata)
                    records.append(record)

                if records:
                    self.index.upsert_records(namespace, records)

            logger.info(f"Namespace '{namespace}' updated successfully!")

        except Exception as e:
            logger.error(f"Failed to upsert files from {folder_path} into namespace '{namespace}': {e}", exc_info=True)

    def describe_index(self):
        """Return index statistics."""
        try:
            stats = self.index.describe_index_stats()
            logger.info(f"Index stats: {stats}")
            return stats
        except Exception as e:
            logger.error(f"Failed to describe index '{self.index_name}': {e}", exc_info=True)
            return None
    def delete_index(self):
   
        try:
            if self.pc.has_index(self.index_name):
                self.pc.delete_index(self.index_name)
                logger.info(f"Pinecone index '{self.index_name}' deleted successfully!")
            else:
                logger.warning(f"Index '{self.index_name}' does not exist.")
        except Exception as e:
            logger.error(f"Failed to delete index '{self.index_name}': {e}", exc_info=True)


            

# ---------------- Exported instance ----------------
# pinecone_worker = PineconeWorker()
# pinecone_worker.delete_index()

# # Example usage:
# # pinecone_worker.upsert_json_folder(PARA_DIR, "pdf-paragraphs")
# # pinecone_worker.upsert_json_folder(TABLE_DIR, "pdf-tables")
# # pinecone_worker.upsert_json_folder(IMAGE_DIR, "pdf-images")
# pinecone_worker.delete_index()
