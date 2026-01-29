"""
PR Fix Agent Core Library
Production-ready components for error analysis and security validation
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
    OllamaAgent,
    PRErrorFixer
)
from .trust_boundary import (
    DryRunMode,
    FixIntent,
    FixAction
)

__all__ = [
    # Security
    'SecurityError',
    'SecurityValidator',
    'InputValidator',
    'RateLimiter',
    # Analysis
    'PRErrorAnalyzer',
    'ErrorStatistics',
    'OllamaAgent',
    'PRErrorFixer',
    # Trust Boundary
    'DryRunMode',
    'FixIntent',
    'FixAction',
]

__version__ = '1.0.0'
__author__ = 'PR Fix Agent Team'
