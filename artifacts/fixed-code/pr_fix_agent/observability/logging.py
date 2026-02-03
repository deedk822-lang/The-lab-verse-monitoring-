"""
Structured Logging Configuration
"""

from __future__ import annotations

import logging
import sys

import structlog

from pr_fix_agent.core.config import Settings


def configure_logging(settings: Settings) -> None:
    """
    Configure structured logging with structlog.
    """

    def get_level(level_name):
        try:
            return getattr(logging, level_name)
        except AttributeError:
            raise ValueError(f"Invalid log level: {level_name}")

    def setup_log_format():
        if settings.log_format == "json":
            processors = [
                structlog.processors.JSONRenderer(),
            ]
        else:
            processors = [
                structlog.dev.ConsoleRenderer(),
            ]

        return processors

    logging.basicConfig(
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
        stream=sys.stdout,
        level=get_level(settings.log_level),
    )

    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]

    processors = setup_log_format() + shared_processors

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )