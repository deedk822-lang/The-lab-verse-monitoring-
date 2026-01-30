"""
PR Fix Agent Core Library
Production-ready components for error analysis, security validation, and automated fixing
"""

from .analyzer import PRErrorAnalyzer, PRErrorFixer
from .models import ModelSelector, ModelSpec
from .observability import BudgetExceededError, CostTracker, LLMCost, ObservableOllamaAgent
from .ollama_agent import OllamaAgent, OllamaQueryError
from .orchestrator import CodeReviewOrchestrator
from .security import InputValidator, RateLimiter, SecurityError, SecurityValidator

__all__ = [
    # Security
    "SecurityError",
    "SecurityValidator",
    "InputValidator",
    "RateLimiter",
    # Analysis & Fixing
    "PRErrorAnalyzer",
    "PRErrorFixer",
    "OllamaAgent",
    "OllamaQueryError",
    # Observability
    "CostTracker",
    "LLMCost",
    "BudgetExceededError",
    "ObservableOllamaAgent",
    # Models
    "ModelSpec",
    "ModelSelector",
    # Orchestration
    "CodeReviewOrchestrator",
]

__version__ = "1.0.0"
__author__ = "PR Fix Agent Team"
