"""
Observability Module
Re-exports consolidated components from ollama_agent.py
"""

import logging

# Reconfigure structured logging for consistent output
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

logger = structlog.get_logger()

# Re-exports for compatibility
from .ollama_agent import (
    BudgetExceededError,  # Example error class with a docstring explaining its purpose
    CostTracker,        # Example cost tracker class with a docstring explaining its purpose
    LLMCost,            # Example LLM cost class with a docstring explaining its purpose
    ObservableOllamaAgent  # Example observable Ollama agent class with a docstring explaining its purpose
)

# Additional security measures can be added here if necessary