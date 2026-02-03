"""
PR Fix Agent Core Library
Production-ready components for error analysis and security validation
"""

from .analyzer import ErrorStatistics as PRErrorAnalyzer
from .security import InputValidator, RateLimiter, SecurityError as PRSecurityError

__all__ = [
    # Security
    'PRSecurityError',
    'InputValidator',
    'RateLimiter',
    # Analysis
    'PRErrorAnalyzer',
]

__version__ = '1.0.0'
__author__ = 'PR Fix Agent Team'