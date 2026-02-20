import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logging(level=logging.INFO, log_file="agent.log"):
    """
    Configures a rotating file handler for the root logger.
    This ensures all logs (including Codex streaming output) are persisted.
    """
    logger = logging.getLogger()
    # Ensure level is set appropriately
    # logger.setLevel(level) # Avoid overriding Celery's level if possible, just ensure handler captures relevant logs
    
    # Create handler
    file_handler = RotatingFileHandler(
        log_file, maxBytes=10*1024*1024, backupCount=5, encoding="utf-8"
    )
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    
    # Avoid adding duplicate handlers if re-imported
    if not any(isinstance(h, RotatingFileHandler) and h.baseFilename.endswith(log_file) for h in logger.handlers):
        logger.addHandler(file_handler)
        logger.info(f"Logging configured: Writing to {os.path.abspath(log_file)}")
