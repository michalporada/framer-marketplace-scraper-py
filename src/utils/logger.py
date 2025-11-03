"""Structured logging configuration using structlog."""

import logging
import sys
from pathlib import Path
from typing import Optional

import structlog
from structlog.stdlib import LoggerFactory

from src.config.settings import settings


def configure_logging() -> None:
    """Configure structured logging for the application."""
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    # Configure handlers: both stdout and file
    handlers = [logging.StreamHandler(sys.stdout)]

    # Add file handler if log file path is configured
    log_file = getattr(settings, "log_file", None)
    if log_file:
        log_path = logs_dir / log_file
        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        handlers.append(file_handler)
    else:
        # Default log file: scraper.log
        default_log_file = logs_dir / "scraper.log"
        file_handler = logging.FileHandler(default_log_file, encoding="utf-8")
        handlers.append(file_handler)

    # Configure logging with handlers
    logging.basicConfig(
        format="%(message)s",
        handlers=handlers,
        level=log_level,
    )

    # Configure structlog
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    # Add JSON formatter if JSON format is requested
    if settings.log_format.lower() == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.extend(
            [
                structlog.dev.ConsoleRenderer(),
            ]
        )

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: Optional[str] = None) -> structlog.stdlib.BoundLogger:
    """Get a configured logger instance.

    Args:
        name: Logger name (usually __name__ from the calling module)

    Returns:
        Configured structlog logger
    """
    if name is None:
        name = "scraper"
    return structlog.get_logger(name)


# Configure logging on module import
configure_logging()

# Default logger
logger = get_logger("scraper")
