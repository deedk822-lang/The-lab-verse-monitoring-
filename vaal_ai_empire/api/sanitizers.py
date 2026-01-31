"""
Input sanitization utilities for security.
Prevents prompt injection and other security issues.
"""

import logging
import re
import unicodedata
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

# Dangerous patterns to detect/block
DANGEROUS_PATTERNS = [
    r"(?i)(ignore|forget|disregard)\s+(all\s+|everything\s+|previous\s+|above\s+|the\s+|these\s+|any\s+|safety\s*)*(instructions|prompts|rules|commands|guidelines|safety|everything)",
    r"(?i)system\s*:\s*you\s+are",
    r"(?i)new\s+(instructions|rules|prompt|commands)",
    r"(?i)(execute|run|eval)\s*\(",
    r"<\s*script\s*>",
    r"javascript\s*:",
    r"<\|im_start\|>",
    r"<\|im_end\|>",
    r"\[INST\]",
    r"\[/INST\]",
]


class PromptInjectionError(ValueError):
    """Exception raised when a prompt injection attempt is detected."""
    pass


def normalize_unicode(text: str) -> str:
    """Normalize unicode to NFKC to prevent obfuscation."""
    return unicodedata.normalize('NFKC', text)


def detect_injection_patterns(text: str) -> List[str]:
    """Detect dangerous patterns in text."""
    normalized = normalize_unicode(text)
    matches = []
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, normalized):
            matches.append(pattern)
    return matches


def sanitize_prompt(
    prompt: str,
    max_length: int = 10000,
    strict: bool = True,
    allow_system_messages: bool = True
) -> str:
    """
    Sanitize user prompts to prevent injection attacks.
    """
    if not prompt:
        return ""

    # Truncate to max length
    if len(prompt) > max_length:
        logger.warning(f"Prompt truncated from {len(prompt)} to {max_length} chars")
        prompt = prompt[:max_length] + "..."

    normalized = normalize_unicode(prompt)

    if not allow_system_messages:
        normalized = normalized.replace("<|im_start|>", "").replace("<|im_end|>", "")

    # Check for dangerous patterns
    matches = detect_injection_patterns(normalized)
    if matches:
        logger.error(f"Dangerous patterns detected: {matches}")
        if strict:
            raise PromptInjectionError("Prompt contains potentially unsafe content")
        else:
            # Filter matches
            for pattern in DANGEROUS_PATTERNS:
                normalized = re.sub(pattern, "[FILTERED]", normalized)

    # Remove null bytes
    normalized = normalized.replace('\x00', '')

    return normalized.strip()


def sanitize_context(context: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively sanitize context dictionary."""
    sanitized = {}
    for key, value in context.items():
        if isinstance(value, str):
            sanitized[key] = sanitize_prompt(value, strict=False)
        elif isinstance(value, dict):
            sanitized[key] = sanitize_context(value)
        else:
            sanitized[key] = value
    return sanitized


def sanitize_webhook_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Sanitize webhook payload to prevent injection."""
    return sanitize_context(payload)


class RateLimiter:
    """Base class for rate limiting."""
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds

    async def is_allowed(self, key: str) -> bool:
        raise NotImplementedError()


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filenames to prevent directory traversal.

    Args:
        filename: Input filename

    Returns:
        Sanitized filename
    """
    # Remove path separators
    filename = filename.replace('/', '').replace('\\', '')

    # Remove dangerous characters
    filename = re.sub(r'[^a-zA-Z0-9._-]', '', filename)

    # Remove leading dots
    filename = filename.lstrip('.')

    return filename[:255]  # Max filename length
