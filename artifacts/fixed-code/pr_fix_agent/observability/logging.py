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
    # Initialize structlog logger factory
    log_factory = structlog.stdlib.LoggerFactory()

    # Create a custom logger class to handle context variables, level, and logger name
    class CustomLogger(structlog.stdlib.BoundLogger):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.contextvars.update({"user_id": "12345"})

    # Set up the structured loggers with custom context variables
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            CustomLogger,
        ],
        wrapper_class=CustomLogger,
        context_class=dict,
        logger_factory=log_factory,
        cache_logger_on_first_use=True,
    )

# Example usage
if __name__ == "__main__":
    settings = Settings(log_level="info", log_format="json")
    configure_logging(settings)