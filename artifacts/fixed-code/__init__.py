"""
PR Fix Agent Core Library
Production-ready components for error analysis and security validation
"""

from typing import *
from .analyzer import ErrorStatistics, PRErrorAnalyzer
from .security import InputValidator, RateLimiter, SecurityError, SecurityValidator

__all__ = [
    # Security
    "SecurityError",
    "SecurityValidator",
    "InputValidator",
    "RateLimiter",
    # Analysis
    "PRErrorAnalyzer",
    "ErrorStatistics",
]

__version__ = "1.0.0"
__author__ = "PR Fix Agent Team"

def safe_import(module_name):
    try:
        return __import__(module_name)
    except ImportError as e:
        print(f"Failed to import {module_name}: {e}")
        return None

# Import modules safely
input_validator = safe_import('InputValidator')
rate_limiter = safe_import('RateLimiter')
security_error = safe_import('SecurityError')
security_validator = safe_import('SecurityValidator')

if input_validator and rate_limiter and security_error and security_validator:
    __all__.extend([
        "input_validator",
        "rate_limiter",
        "security_error",
        "security_validator",
    ])