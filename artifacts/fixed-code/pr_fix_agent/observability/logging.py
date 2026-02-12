"""
Structured Logging Configuration
"""

from __future__ import annotations

import logging
import sys

import structlog

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pr_fix_agent.core.config import Settings


def configure_logging(settings: Settings) -> None:
    """
    Configure structured logging with structlog.
    """

    # Use a safer format string
    formatter = structlog.stdlib.TextFormatter(fmt="%(message)s")

    # Validate the log level before setting it
    valid_levels = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    if settings.log_level not in valid_levels:
        raise ValueError(f"Invalid log level: {settings.log_level}")

    # Configure the logger
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            formatter,  # Use the configured formatter
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )