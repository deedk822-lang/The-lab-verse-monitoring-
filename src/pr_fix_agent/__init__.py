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
from .ollama_agent import OllamaAgent, OllamaQueryError
from .observability import CostTracker, LLMCost, BudgetExceededError, ObservableOllamaAgent
from .models import ModelSpec, ModelSelector
from .orchestrator import CodeReviewOrchestrator

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
    'OllamaQueryError',
    # Observability
    'CostTracker',
    'LLMCost',
    'BudgetExceededError',
    'ObservableOllamaAgent',
    # Models
    'ModelSpec',
    'ModelSelector',
    # Orchestration
    'CodeReviewOrchestrator',
]

__version__ = '1.0.0'
__author__ = 'PR Fix Agent Team'
