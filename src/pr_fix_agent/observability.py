"""
Observability Module
Re-exports consolidated components from ollama_agent.py
"""

import logging

import structlog

# Re-export from ollama_agent
from .ollama_agent import BudgetExceededError, CostTracker, LLMCost, OllamaAgent

# Alias for backward compatibility if needed
ObservableOllamaAgent = OllamaAgent

__all__ = [
    'BudgetExceededError',
    'CostTracker',
    'LLMCost',
    'OllamaAgent',
    'ObservableOllamaAgent',
    'logger',
    'configure_structured_logging',
]


# Re-configure structured logging for consistent output
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
