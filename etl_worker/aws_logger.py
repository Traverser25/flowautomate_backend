import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logger(name):
    # Basic logging configuration
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
    os.makedirs(log_dir, exist_ok=True)

    log_file = os.path.join(log_dir, 'app.log')
    log_level = logging.INFO
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    max_size_mb = 5
    backup_count = 3

    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(log_level)

    # Create rotating file handler
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=max_size_mb * 1024 * 1024,
        backupCount=backup_count
    )

    # Create console handler
    console_handler = logging.StreamHandler()

    # Formatter
    formatter = logging.Formatter(log_format)
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Avoid adding duplicate handlers if already exists
    if not logger.handlers:
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger
