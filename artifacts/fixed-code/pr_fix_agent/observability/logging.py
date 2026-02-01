"""
Structured Logging Configuration - Global Production Standard
Datadog-compatible JSON logging using structlog.
"""

import logging
import sys
from typing import Any, Dict

import structlog

def configure_structured_logging(level: int = logging.INFO):
    """
    Configure structured logging for the entire application.

    ✅ JSON format
    ✅ Timestamping
    ✅ Level addition
    ✅ Context merging
    """
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer()
        ],
        wrapper_class=structlog.make_filtering_bound_logger(level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure standard logging to use structlog
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=level,
    )
