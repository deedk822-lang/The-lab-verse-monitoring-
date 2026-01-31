"""
Input sanitization utilities for security.
Prevents prompt injection and other security issues.
"""

import logging
<<<<<<< HEAD
import threading
import time
import unicodedata
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

# Refined regex for prompt injection
INJECTION_PATTERN = re.compile(
    r"(?i)(ignore|forget|disregard|reveal|reveal|delete|system|inst)\s+(?:.*?\s+)?(instructions|prompts|rules|everything|above|all|guidelines|secrets|message|start|end)",
    re.UNICODE
)

# Additional specific patterns for detection
DETECTION_PATTERNS = [
    INJECTION_PATTERN,
    re.compile(r"(?i)system\s*:\s*you\s+are"),
    re.compile(r"<\|im_start\|>system"),
    re.compile(r"\[INST\].*?\[/INST\]", re.DOTALL)
=======
import re
import unicodedata
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

# Dangerous patterns to detect/block
DANGEROUS_PATTERNS = [
    r"(?i)(ignore|forget|disregard)\s+(previous|above|all)\s+(instructions|prompts|rules)",
    r"(?i)system\s*:\s*you\s+are",
    r"(?i)new\s+(instructions|rules|prompt)",
    r"(?i)(execute|run|eval)\s*\(",
    r"<\s*script\s*>",
    r"javascript\s*:",
    r"<\|im_start\|>",
    r"<\|im_end\|>",
    r"\[INST\]",
    r"\[/INST\]",
>>>>>>> main
]

SYSTEM_MESSAGE_PATTERN = re.compile(r"<\|im_start\|>system|<\|im_end\|>")

<<<<<<< HEAD

class PromptInjectionDetected(Exception):
    """Raised when a prompt injection pattern is detected."""
=======
class PromptInjectionDetected(ValueError):
    """Exception raised when a prompt injection attempt is detected."""
>>>>>>> main
    pass


def normalize_unicode(text: str) -> str:
<<<<<<< HEAD
    """Normalize unicode to prevent obfuscation."""
    return unicodedata.normalize('NFKC', text)


def detect_injection_patterns(prompt: str) -> List[str]:
    """Detect prompt injection patterns."""
    normalized = normalize_unicode(prompt)
    found = []
    for pattern in DETECTION_PATTERNS:
        matches = pattern.findall(normalized)
        if matches:
            found.extend([str(m) for m in matches])
    return found
=======
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
>>>>>>> main


def sanitize_prompt(
    prompt: str,
    max_length: int = 10000,
<<<<<<< HEAD
    strict: bool = False,
=======
    strict: bool = True,
>>>>>>> main
    allow_system_messages: bool = True
) -> str:
    """
    Sanitize user prompts to prevent injection attacks.
    """
    if not prompt:
        return ""
<<<<<<< HEAD
    
    # Truncate
    if len(prompt) > max_length:
        prompt = prompt[:max_length] + "..."
    
    # Detect injection
    if detect_injection_patterns(prompt):
        if strict:
            raise PromptInjectionDetected("Malicious pattern detected")
        else:
            # Soft filtering
            for pattern in DETECTION_PATTERNS:
                prompt = pattern.sub("[FILTERED]", prompt)

    # System messages
    if not allow_system_messages:
        prompt = SYSTEM_MESSAGE_PATTERN.sub("", prompt)

    # Remove null bytes
    prompt = prompt.replace('\x00', '')
    
    return prompt


def sanitize_context(context: Dict[str, Any]) -> Dict[str, Any]:
    """Sanitize context dictionary recursively."""
    sanitized = {}
    for k, v in context.items():
        if isinstance(v, str):
            sanitized[k] = sanitize_prompt(v, strict=False)
        elif isinstance(v, dict):
            sanitized[k] = sanitize_context(v)
        else:
            sanitized[k] = v
    return sanitized


def sanitize_webhook_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Sanitize webhook payload."""
    return sanitize_context(payload)


class RateLimiter:
    """Thread-safe rate limiter."""

    def __init__(self, max_requests: int = 100, window_seconds: int = 3600):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: List[float] = []
        self._lock = threading.Lock()

    def is_allowed(self, key: str) -> bool:
        """Check if request is allowed."""
        return self.check_rate_limit()

    def check_rate_limit(self) -> bool:
        """Check if rate limit is exceeded."""
        now = time.time()
        with self._lock:
            self.requests = [
                req for req in self.requests
                if now - req < self.window_seconds
            ]
            if len(self.requests) >= self.max_requests:
                return False
            self.requests.append(now)
            return True

    def get_stats(self) -> Dict[str, Any]:
        """Get stats."""
        with self._lock:
            return {
                "remaining": self.max_requests - len(self.requests)
            }

    def reset(self):
        """Reset."""
        with self._lock:
            self.requests.clear()
=======

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
            raise PromptInjectionDetected("Prompt contains potentially unsafe content")
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
>>>>>>> main
