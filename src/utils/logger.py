"""
Global logger configuration with colored output for the Resume Indexer application.
"""

import logging
import sys
from typing import Optional
from datetime import datetime


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colored output for different log levels."""

    # ANSI color codes
    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
        "RESET": "\033[0m",  # Reset
        "BOLD": "\033[1m",  # Bold
        "DIM": "\033[2m",  # Dim
    }

    def __init__(self, include_colors: bool = True):
        """
        Initialize the colored formatter.

        Args:
            include_colors: Whether to include color codes in output
        """
        self.include_colors = include_colors
        super().__init__()

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record with colors and structured layout."""
        # Create a copy to avoid modifying the original record
        record_copy = logging.makeLogRecord(record.__dict__)

        # Format timestamp
        timestamp = datetime.fromtimestamp(record_copy.created).strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        # Get color for log level
        level_color = self.COLORS.get(record_copy.levelname, "")
        reset_color = self.COLORS["RESET"]
        bold = self.COLORS["BOLD"]
        dim = self.COLORS["DIM"]

        # Don't use colors if disabled or not in a terminal
        if not self.include_colors or not sys.stderr.isatty():
            level_color = reset_color = bold = dim = ""

        # Format logger name (truncate if too long)
        logger_name = record_copy.name
        if len(logger_name) > 20:
            logger_name = "..." + logger_name[-17:]

        # Create the formatted message
        if record_copy.levelname in ["ERROR", "CRITICAL"]:
            # Highlight errors and critical messages
            formatted_message = (
                f"{dim}[{timestamp}]{reset_color} "
                f"{bold}{level_color}[{record_copy.levelname:8}]{reset_color} "
                f"{dim}[{logger_name:20}]{reset_color} "
                f"{bold}{level_color}{record_copy.getMessage()}{reset_color}"
            )
        elif record_copy.levelname == "WARNING":
            # Highlight warnings
            formatted_message = (
                f"{dim}[{timestamp}]{reset_color} "
                f"{level_color}[{record_copy.levelname:8}]{reset_color} "
                f"{dim}[{logger_name:20}]{reset_color} "
                f"{level_color}{record_copy.getMessage()}{reset_color}"
            )
        else:
            # Normal formatting for INFO and DEBUG
            formatted_message = (
                f"{dim}[{timestamp}]{reset_color} "
                f"{level_color}[{record_copy.levelname:8}]{reset_color} "
                f"{dim}[{logger_name:20}]{reset_color} "
                f"{record_copy.getMessage()}"
            )

        # Add exception info if present
        if record_copy.exc_info:
            exception_text = self.formatException(record_copy.exc_info)
            formatted_message += f"\n{level_color}{exception_text}{reset_color}"

        return formatted_message


def setup_logger(
    name: str = "resume-indexer",
    level: str = "INFO",
    include_colors: bool = True,
    log_file: Optional[str] = None,
) -> logging.Logger:
    """
    Set up a logger with colored console output and optional file logging.

    Args:
        name: Logger name
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        include_colors: Whether to include colors in console output
        log_file: Optional path to log file

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Clear any existing handlers to avoid duplicates
    logger.handlers.clear()

    # Set log level
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(numeric_level)

    # Create console handler with colored output
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(numeric_level)
    console_formatter = ColoredFormatter(include_colors=include_colors)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # Create file handler if specified
    if log_file:
        try:
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(numeric_level)
            # File logs don't need colors
            file_formatter = ColoredFormatter(include_colors=False)
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            logger.warning(f"Could not create file handler for {log_file}: {e}")

    # Prevent propagation to root logger to avoid duplicate messages
    logger.propagate = False

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for the given name.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


# Initialize the root application logger
def configure_application_logging(
    level: str = "INFO", include_colors: bool = True, log_file: Optional[str] = None
) -> None:
    """
    Configure application-wide logging.

    Args:
        level: Log level for the application
        include_colors: Whether to include colors in console output
        log_file: Optional path to log file
    """
    # Set up the root logger for the application
    root_logger = setup_logger(
        name="resume-indexer",
        level=level,
        include_colors=include_colors,
        log_file=log_file,
    )

    # Configure specific loggers for different components
    loggers_config = {
        "uvicorn": "INFO",
        "uvicorn.error": "INFO",
        "uvicorn.access": "WARNING",  # Reduce access log verbosity
        "fastapi": "INFO",
        "httpx": "WARNING",
        "httpcore": "WARNING",
        "openai": "WARNING",
        "pinecone": "INFO",
        "motor": "WARNING",
        "pymongo": "WARNING",
    }

    for logger_name, logger_level in loggers_config.items():
        logger = logging.getLogger(logger_name)
        logger.setLevel(getattr(logging, logger_level.upper()))
        # Let these loggers use the same handlers as the root logger
        logger.propagate = True

    root_logger.info("Logging configuration complete")
    root_logger.info(f"Log level set to: {level}")
    if log_file:
        root_logger.info(f"Logging to file: {log_file}")


# Example usage and testing
if __name__ == "__main__":
    # Test the logger
    configure_application_logging(level="DEBUG", include_colors=True)

    logger = get_logger(__name__)

    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")

    try:
        raise ValueError("Test exception")
    except Exception as e:
        logger.error("An exception occurred", exc_info=True)
