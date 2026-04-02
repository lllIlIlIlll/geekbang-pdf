"""Logging configuration for GeekBang PDF Saver."""

import logging
import sys
from typing import Optional


def setup_logging(level: str = "INFO") -> logging.Logger:
    """Setup and configure the logger.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger("geekbang_pdf")
    logger.setLevel(getattr(logging, level.upper()))

    # Avoid duplicate handlers if called multiple times
    if not logger.handlers:
        console = logging.StreamHandler(sys.stdout)
        console.setFormatter(
            logging.Formatter("%(levelname)s: %(message)s")
        )
        logger.addHandler(console)

    return logger


# Global logger instance
logger = setup_logging()


def set_log_level(level: str) -> None:
    """Change the log level.

    Args:
        level: New log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    logger.setLevel(getattr(logging, level.upper()))
    for handler in logger.handlers:
        handler.setLevel(getattr(logging, level.upper()))
