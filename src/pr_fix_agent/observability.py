"""
Observability Module
Re-exports consolidated components from agents.ollama to maintain compatibility.
"""

from pr_fix_agent.agents.ollama import BudgetExceededError, CostTracker, LLMCost, OllamaAgent as ObservableOllamaAgent
from pr_fix_agent.observability.logging import configure_structured_logging

 enterprise-upgrade-14295437577485996612
__all__ = [
    'BudgetExceededError',
    'CostTracker',
    'LLMCost',
    'ObservableOllamaAgent',
    'configure_structured_logging'
]

import structlog


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

# Re-exports for compatibility
from .ollama_agent import (
    BudgetExceededError,
    CostTracker,
    LLMCost,
    OllamaAgent as ObservableOllamaAgent
)
 main
