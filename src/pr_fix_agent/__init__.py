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
    ErrorStatistics,
    PRErrorFixer
)
from .ollama_agent_fixed import OllamaAgent
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
    'ErrorStatistics',
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

__version__ = '1.0.0'
__author__ = 'PR Fix Agent Team'
