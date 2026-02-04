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

        # Ensure we have a valid and unique request ID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id

        # Set security headers
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains; preload"
        )
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none';";
        )
        response.headers["X-XSS-Protection"] = (
            "1; mode=block"
        )
        response.headers["Referrer-Policy"] = "origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "geolocation=(self), microphone=(self), camera=(self)"
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

        # Log the request details
        logger.info(
            "request_received",
            method=method,
            path=path,
            request_id=request_id,
            client_ip=client_ip,
        )

        response = await call_next(request)

        # Log the response details
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