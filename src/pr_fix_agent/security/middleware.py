"""
Security Middleware - S4: Comprehensive Security Headers
"""

from __future__ import annotations

import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import structlog

logger = structlog.get_logger()


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    S4: Add comprehensive security headers to all responses.

    Headers:
    - Strict-Transport-Security (HSTS)
    - Content-Security-Policy (CSP)
    - X-Content-Type-Options
    - X-Frame-Options
    - X-XSS-Protection
    - Referrer-Policy
    - Permissions-Policy
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Response]
    ) -> Response:
        response = await call_next(request)

        # HSTS: Force HTTPS for 1 year
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains; preload"
        )

        # CSP: Restrict content sources
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )

        # Prevent MIME-type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # Enable XSS protection
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Control referrer information
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions policy (disable unnecessary features)
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=()"
        )

        return response


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Add unique request ID for tracing."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Response]
    ) -> Response:
        # Generate or extract request ID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

        # Add to request state
        request.state.request_id = request_id

        # Process request
        response = await call_next(request)

        # Add to response headers
        response.headers["X-Request-ID"] = request_id

        return response


class AuditLoggingMiddleware(BaseHTTPMiddleware):
    """
    S5: Audit logging middleware.

    Logs all privileged operations to immutable audit.log.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Response]
    ) -> Response:
        # Get request details
        method = request.method
        path = request.url.path
        request_id = getattr(request.state, "request_id", "unknown")
        client_ip = request.client.host if request.client else "unknown"

        # Log request
        logger.info(
            "request_received",
            method=method,
            path=path,
            request_id=request_id,
            client_ip=client_ip,
        )

        # Process request
        response = await call_next(request)

        # Log response
        logger.info(
            "request_completed",
            method=method,
            path=path,
            status_code=response.status_code,
            request_id=request_id,
            client_ip=client_ip,
        )

        # Check if this is a privileged operation
        privileged_paths = ["/admin", "/api/v1/admin"]
        is_privileged = any(path.startswith(p) for p in privileged_paths)

        if is_privileged:
            # Log to audit trail (S5)
            from pr_fix_agent.security.audit import get_audit_logger

            audit_logger = get_audit_logger()
            audit_logger.log_event(
                event_type="api_access",
                actor_id=getattr(request.state, "user_id", "anonymous"),
                actor_ip=client_ip,
                resource=path,
                action=method,
                result="success" if response.status_code < 400 else "failure",
                request_id=request_id,
                metadata={"status_code": response.status_code},
            )

        return response
