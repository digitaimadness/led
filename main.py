"""Main entry point for Asus TUF utilities."""

import logging
from logging.handlers import RotatingFileHandler
import sys
from tuf_utils import TUFUtils

def setup_logging():
    """Set up logging configuration."""
    logger = logging.getLogger('TUFUtils')
    logger.setLevel(logging.INFO)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    
    # File handler
    file_handler = RotatingFileHandler('tuf_utils.log', maxBytes=1024*1024, backupCount=5)
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

def main():
    """Main entry point."""
    setup_logging()
    logger = logging.getLogger('TUFUtils')
    
    try:
        utils = TUFUtils()
        utils.start()
    except Exception as e:
        logger.error(f"Failed to start TUF utilities: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
