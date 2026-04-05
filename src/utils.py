"""
Logging configuration and utilities.
"""
import logging
from pathlib import Path
from datetime import datetime

from src.config import LOGS_DIR


def setup_logging(name: str = "videoai", level: int = logging.INFO):
    """
    Setup logging for a module.

    Args:
        name: Logger name
        level: Logging level

    Returns:
        Logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid duplicate handlers
    if logger.handlers:
        return logger

    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    # File handler
    log_file = LOGS_DIR / f"{name}_{datetime.now():%Y%m%d}.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(level)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)

    # Formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """Get logger instance."""
    return logging.getLogger(name)
