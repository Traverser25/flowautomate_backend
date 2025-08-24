# app/core/logger.py
import logging
from logging.handlers import RotatingFileHandler
import os

LOG_DIR = os.path.join(os.getcwd(), "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "app.log")


def get_logger(name: str = __name__, level: int = logging.INFO) -> logging.Logger:
    """
    Returns a reusable logger instance.
    Logs both to console and rotating file.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        console_handler.setFormatter(console_formatter)

        # File handler (rotating)
        file_handler = RotatingFileHandler(LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3)
        file_handler.setLevel(level)
        file_handler.setFormatter(console_formatter)

        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

    return logger
