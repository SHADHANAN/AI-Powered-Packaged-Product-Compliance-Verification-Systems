import logging
import sys
from typing import Optional


class StructuredFormatter(logging.Formatter):
    """Custom formatter to format log records with consistent structure."""

    DEFAULT_FMT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    DATE_FMT = "%Y-%m-%d %H:%M:%S"

    def __init__(self, fmt: Optional[str] = None, datefmt: Optional[str] = None):
        super().__init__(fmt=fmt or self.DEFAULT_FMT, datefmt=datefmt or self.DATE_FMT)


def setup_logging(log_level: str = "INFO") -> None:
    """Configure structured logging for the application and standard libraries."""
    level = getattr(logging, log_level.upper(), logging.INFO)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove existing handlers to avoid duplicate log entries
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    # Console handler with structured formatting
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(StructuredFormatter())

    root_logger.addHandler(console_handler)

    # Set appropriate levels for 3rd party loggers
    logging.getLogger("uvicorn.access").handlers = [console_handler]
    logging.getLogger("uvicorn.error").handlers = [console_handler]


def get_logger(name: str = "app") -> logging.Logger:
    """Retrieve a named logger instance."""
    return logging.getLogger(name)
