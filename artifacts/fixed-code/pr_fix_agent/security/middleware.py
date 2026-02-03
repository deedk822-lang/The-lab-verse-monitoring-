"""
Security Middleware - S4: Comprehensive Security Headers
"""

from __future__ import annotations

import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from structlog import get_logger

logger = get_logger()


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

        # Properly formatted Content-Security-Policy
        csp = (
            "default-src 'self'; "
            "script-src 'self' https://example.com; "
            "style-src 'self' https://example.com; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )
        response.headers["Content-Security-Policy"] = csp

        # X-Frame-Options middleware
        response.headers["X-Frame-Options"] = "SAMEORIGIN"

        # X-Content-Type-Options middleware
        response.headers["X-Content-Type-Options"] = "nosniff"

        # X-XSS-Protection middleware
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Referrer-Policy middleware
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions-Policy middleware
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
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


class AuditLoggingMiddleware(BaseHTTPMiddleware):
    """
    S5: Audit logging middleware.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Response]
    ) -> Response:
        method = request.method
        path = request.url.path
        request_id = getattr(request.state, "request_id", "unknown")
        client_ip = request.client.host if request.client else "unknown"

        logger.info(
            "request_received",
            method=method,
            path=path,
            request_id=request_id,
            client_ip=client_ip,
        )

        response = await call_next(request)

        logger.info(
            "request_completed",
            method=method,
            path=path,
            status_code=response.status_code,
            request_id=request_id,
            client_ip=client_ip,
        )

        privileged_paths = ["/admin", "/api/v1/admin"]
        is_privileged = any(path.startswith(p) for p in privileged_paths)

        if is_privileged:
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