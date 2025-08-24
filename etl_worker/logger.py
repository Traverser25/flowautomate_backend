import logging
from pymongo import MongoClient
from dotenv import load_dotenv
import os


class MongoDBLogger(logging.Handler):
    def __init__(self, collection_name):
        super().__init__()
        
        # Load environment variables
        load_dotenv()
        
        # MongoDB connection
        self.mongo_url = os.getenv("MONGO_URL")
        if not self.mongo_url:
            raise Exception("MONGO_URL is not set in the .env file")
        
        self.client = MongoClient(self.mongo_url)
        self.db = self.client['tenderwin_db']
        self.collection = self.db[collection_name]

    def emit(self, record):
        """Emit a record to MongoDB."""
        try:
            log_entry = self.format(record)
            self.collection.insert_one({"log": log_entry, "level": record.levelname, "time": record.created})
        except Exception as e:
            print(f"Failed to log to MongoDB: {e}")

    def close(self):
        """Close the MongoDB connection."""
        self.client.close()
        super().close()

# Example usage
if __name__ == "__main__":
    logger = logging.getLogger("MongoDBLogger")
    logger.setLevel(logging.DEBUG)
    
    mongo_logger = MongoDBLogger("logger_coln")  # Collection to store logs
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    mongo_logger.setFormatter(formatter)
    
    logger.addHandler(mongo_logger)
    
    logger.info("This is an info message.")
    logger.error("This is an error message.")
