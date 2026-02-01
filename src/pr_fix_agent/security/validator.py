"""
Security validators and middleware
"""

import asyncio
import hashlib
import ipaddress
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set
from urllib.parse import urlparse

import redis.asyncio as redis
from pydantic import BaseModel, Field, field_validator

from ..core.config import settings


class SecurityError(Exception):
    """Base security exception"""
    pass


class InputValidationError(SecurityError):
    """Input validation error"""
    pass


class RateLimitError(SecurityError):
    """Rate limit exceeded error"""
    pass


class SSRFError(SecurityError):
    """SSRF protection error"""
    pass


class SecurityValidator:
    """Security validator for inputs and requests"""

    # Dangerous patterns
    DANGEROUS_PATTERNS = [
        r"(?i)(eval|exec|system|subprocess|os\.|import\s+os)",
        r"(?i)(__import__|getattr|setattr|delattr)",
        r"(?i)(open\(|file\(|input\()",
        r"(?i)(requests\.|urllib\.|http\.client)",
        r"(?i)(socket\.|ssl\.|ftplib\.|smtplib\.)",
        r"(?i)(subprocess\.|os\.system|os\.popen)",
    ]

    def __init__(self):
        self.dangerous_patterns = [re.compile(pattern) for pattern in self.DANGEROUS_PATTERNS]

    def validate_input(self, input_text: str, max_length: Optional[int] = None) -> str:
        """Validate input text for security issues"""
        if not input_text:
            raise InputValidationError("Input cannot be empty")

        if max_length and len(input_text) > max_length:
            raise InputValidationError(f"Input too long (max {max_length} characters)")

        # Check for dangerous patterns
        for pattern in self.dangerous_patterns:
            if pattern.search(input_text):
                raise InputValidationError("Input contains potentially dangerous code")

        return input_text

    def validate_url(self, url: str) -> str:
        """Validate URL for SSRF protection"""
        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                raise SSRFError("Invalid URL format")

            # Check against blocked domains
            domain = parsed.netloc.lower()
            for blocked in settings.security.blocked_domains:
                if blocked in domain:
                    raise SSRFError(f"Domain {domain} is blocked")

            # Check against allowed domains if configured
            if settings.security.allowed_domains:
                allowed = False
                for allowed_domain in settings.security.allowed_domains:
                    if allowed_domain in domain or domain.endswith(f".{allowed_domain}"):
                        allowed = True
                        break
                if not allowed:
                    raise SSRFError(f"Domain {domain} is not in allowed list")

            return url

        except Exception as e:
            raise SSRFError(f"URL validation failed: {e}")

    def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for security"""
        # Remove path separators and dangerous characters
        filename = re.sub(r'[<>:"/\\|?*]', '', filename)
        filename = filename.strip()

        if not filename:
            raise InputValidationError("Invalid filename")

        return filename


class RateLimiter:
    """Redis-based rate limiter"""

    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis = redis_client
        self.requests = settings.security.rate_limit_requests
        self.window = settings.security.rate_limit_window_seconds

    async def is_allowed(self, key: str) -> bool:
        """Check if request is allowed under rate limit"""
        if not self.redis:
            return True  # No rate limiting if Redis not available

        try:
            # Use Redis sorted set to track requests
            now = datetime.utcnow().timestamp()
            window_start = now - self.window

            # Remove old entries
            await self.redis.zremrangebyscore(key, 0, window_start)

            # Count current requests in window
            count = await self.redis.zcount(key, window_start, now)

            if count >= self.requests:
                return False

            # Add current request
            await self.redis.zadd(key, {str(now): now})

            # Set expiration on the key
            await self.redis.expire(key, self.window)

            return True

        except Exception:
            # Fail open if Redis is unavailable
            return True

    async def get_remaining_requests(self, key: str) -> int:
        """Get remaining requests in current window"""
        if not self.redis:
            return self.requests

        try:
            now = datetime.utcnow().timestamp()
            window_start = now - self.window
            count = await self.redis.zcount(key, window_start, now)
            return max(0, self.requests - count)
        except Exception:
            return self.requests


class AuditLogger:
    """Security audit logger"""

    def __init__(self):
        self.redis = None

    async def log_event(
        self,
        event_type: str,
        user_id: Optional[str] = None,
        resource: Optional[str] = None,
        action: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
    ):
        """Log security event"""
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "user_id": user_id,
            "resource": resource,
            "action": action,
            "details": details or {},
            "ip_address": ip_address,
        }

        # In a real implementation, this would write to a secure log store
        # For now, we'll just print to structured log
        import structlog
        logger = structlog.get_logger("security.audit")
        logger.info("Security event", **event)

    async def log_authentication_attempt(
        self,
        user_id: str,
        success: bool,
        ip_address: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Log authentication attempt"""
        await self.log_event(
            event_type="authentication",
            user_id=user_id,
            action="login_attempt",
            details={"success": success, **(details or {})},
            ip_address=ip_address,
        )

    async def log_api_access(
        self,
        user_id: Optional[str],
        endpoint: str,
        method: str,
        status_code: int,
        ip_address: Optional[str] = None,
    ):
        """Log API access"""
        await self.log_event(
            event_type="api_access",
            user_id=user_id,
            resource=endpoint,
            action=f"{method}_{status_code}",
            ip_address=ip_address,
        )