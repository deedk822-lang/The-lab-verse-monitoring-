"""
Observability Module
Re-exports consolidated components from ollama_agent.py
"""

import logging

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
)

# Dynamically import the modules to avoid potential security issues
import importlib.util

def dynamically_import_module(module_name, module_path):
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# Re-export the components from the dynamically imported modules
ollama_agent = dynamically_import_module("ollama_agent", "path/to/ollama_agent.py")
BudgetExceededError = ollama_agent.BudgetExceededError
CostTracker = ollama_agent.CostTracker
LLMCost = ollama_agent.LLMCost

# Re-export the ObservableOllamaAgent class directly from the dynamically imported module
ObservableOllamaAgent = ollama_agent.ObservableOllamaAgent