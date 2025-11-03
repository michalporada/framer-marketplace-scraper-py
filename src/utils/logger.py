"""Structured logging configuration using structlog."""

import logging
import sys
from typing import Optional

import structlog
from structlog.stdlib import LoggerFactory

from src.config.settings import settings


def configure_logging() -> None:
    """Configure structured logging for the application."""
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
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
        processors.extend([
            structlog.dev.ConsoleRenderer(),
        ])

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

