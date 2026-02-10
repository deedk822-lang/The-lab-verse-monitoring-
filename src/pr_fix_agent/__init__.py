"""
PR Fix Agent Core Library
Production-ready components for error analysis, security validation, and automated fixing
"""

from .analyzer import PRErrorAnalyzer, PRErrorFixer
from .models import ModelSelector, ModelSpec
from .observability import BudgetExceededError, CostTracker, LLMCost
from .ollama_agent import OllamaAgent, OllamaQueryError
from .orchestrator import CodeReviewOrchestrator
from .security import InputValidator, RateLimiter, SecurityError, SecurityValidator

__all__ = [
    'BudgetExceededError',
    # Orchestration
    'CodeReviewOrchestrator',
    # Observability
    'CostTracker',
    'InputValidator',
    'LLMCost',
    'ModelSelector',
    # Models
    'ModelSpec',
    'OllamaAgent',
    'OllamaQueryError',
    # Analysis & Fixing
    'PRErrorAnalyzer',
    'PRErrorFixer',
    'RateLimiter',
    # Security
    'SecurityError',
    'SecurityValidator',
]

__version__ = '0.1.0'
__author__ = 'PR Fix Agent Team'
