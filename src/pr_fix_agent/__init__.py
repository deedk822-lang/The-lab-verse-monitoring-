"""
PR Fix Agent Core Library
Production-ready components for error analysis, security validation, and automated fixing
"""

from .security import (
    SecurityError,
    SecurityValidator,
    InputValidator,
    RateLimiter
)
from .analyzer import (
    PRErrorAnalyzer,
    PRErrorFixer
)
from .ollama_agent import OllamaAgent
from .observability import CostTracker, LLMCost, BudgetExceededError
from .models import ModelSpec, ModelSelector
from .orchestrator import Orchestrator

__all__ = [
    # Security
    'SecurityError',
    'SecurityValidator',
    'InputValidator',
    'RateLimiter',
    # Analysis & Fixing
    'PRErrorAnalyzer',
    'PRErrorFixer',
    'OllamaAgent',
    # Observability
    'CostTracker',
    'LLMCost',
    'BudgetExceededError',
    # Models
    'ModelSpec',
    'ModelSelector',
    # Orchestration
    'Orchestrator',
]

__version__ = '0.1.0'
__author__ = 'PR Fix Agent Team'
