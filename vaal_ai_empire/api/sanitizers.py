"""
Input sanitization utilities for security.
Prevents prompt injection and other security issues.
"""

import re
import logging
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
]

SYSTEM_MESSAGE_PATTERN = re.compile(r"<\|im_start\|>system|<\|im_end\|>")


class PromptInjectionDetected(Exception):
    """Raised when a prompt injection pattern is detected."""
    pass


def normalize_unicode(text: str) -> str:
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


def sanitize_prompt(
    prompt: str,
    max_length: int = 10000,
    strict: bool = False,
    allow_system_messages: bool = True
) -> str:
    """
    Sanitize user prompts to prevent injection attacks.
    """
    if not prompt:
        return ""
    
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
