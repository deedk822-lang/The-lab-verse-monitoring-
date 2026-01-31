"""
Observability Module
Re-exports consolidated components from ollama_agent.py
"""

import logging

import structlog

# Re-export from ollama_agent using import
import ollama_agent as _ollama_agent

# Alias for backward compatibility if needed
ObservableOllamaAgent = _ollama_agent.OllamaAgent


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

# Example usage of the re-exported components
try:
    cost_tracker = _ollama_agent.CostTracker()
    budget_exceeded_error = _ollama_agent.BudgetExceededError("High budget")
except BudgetExceededError as e:
    logger.error(e)