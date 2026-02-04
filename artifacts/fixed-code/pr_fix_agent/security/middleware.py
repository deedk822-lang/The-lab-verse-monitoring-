"""
Security Middleware - S4: Comprehensive Security Headers
"""

from __future__ import annotations

from typing import TYPE_CHECKING
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
import structlog

if TYPE_CHECKING:
    from collections.abc import Callable

    from fastapi import Request, Response

logger = structlog.get_logger()


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    S4: Add comprehensive security headers to all responses.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Response]
    ) -> Response:
        response = await call_next(request)

        # Sanitize Content-Security-Policy header
        csp = response.headers.get("Content-Security-Policy", "")
        sanitized_csp = ""
        for directive in csp.split(";"):
            if "script-src" in directive.lower():
                sanitized_csp += (
                    f'script-src {(directive.replace("unsafe-inline", "'self'") if "'unsafe-inline'" not in directive else "")}'
                )
            elif "img-src" in directive.lower():
                sanitized_csp += (
                    f"img-src {'data:' if 'data:' not in directive else ""}"
                )
            else:
                sanitized_csp += directive + ";"
        response.headers["Content-Security-Policy"] = sanitized_csp.strip()

        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains; preload"
        )

        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=()"
        )

        return response