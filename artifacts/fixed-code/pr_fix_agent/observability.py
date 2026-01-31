"""
Observability Module
Re-exports consolidated components from ollama_agent.py
"""

import logging

import structlog

# Reconfigure structured logging for consistent output, ensuring only necessary information is logged
def configure_structured_logging():
    """Configure structured logging (Datadog-compatible)"""
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer()
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

configure_structured_logging()

logger = structlog.get_logger("observable_ollama_agent")

# Re-exports for compatibility
from .ollama_agent import (
    BudgetExceededError,
    CostTracker,
    LLMCost,
    ObservableOllamaAgent
)
