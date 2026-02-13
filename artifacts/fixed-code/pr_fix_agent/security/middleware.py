"""
Security Middleware - S4: Comprehensive Security Headers
"""

from __future__ import annotations

from collections.abc import Callable
import uuid
import re

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import structlog

logger = structlog.get_logger()


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    S4: Add comprehensive security headers to all responses.
    """

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Response]
    ) -> Response:
        response = await call_next(request)

        # Sanitize and validate Content-Security-Policy
        csp = request.headers.get("Content-Security-Policy", "")
        if not re.match(r"^[^;]+(?:;[^;]+)*$", csp):
            logger.error(
                "Invalid Content-Security-Policy header",
                request_id=request.state.request_id,
                client_ip=request.client.host if request.client else "unknown",
            )
            return response

        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            f"script-src '{csp}'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )

        # Sanitize and validate Strict-Transport-Security
        stss = request.headers.get("Strict-Transport-Security", "")
        if not re.match(r"^[^;]+(?:;[^;]+)*$", stss):
            logger.error(
                "Invalid Strict-Transport-Security header",
                request_id=request.state.request_id,
                client_ip=request.client.host if request.client else "unknown",
            )
            return response

        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains; preload"
        )

        # Sanitize and validate X-Content-Type-Options
        xcto = request.headers.get("X-Content-Type-Options", "")
        if not re.match(r"^[^;]+(?:;[^;]+)*$", xcto):
            logger.error(
                "Invalid X-Content-Type-Options header",
                request_id=request.state.request_id,
                client_ip=request.client.host if request.client else "unknown",
            )
            return response

        response.headers["X-Content-Type-Options"] = "nosniff"

        # Sanitize and validate X-Frame-Options
        xfo = request.headers.get("X-Frame-Options", "")
        if not re.match(r"^[^;]+(?:;[^;]+)*$", xfo):
            logger.error(
                "Invalid X-Frame-Options header",
                request_id=request.state.request_id,
                client_ip=request.client.host if request.client else "unknown",
            )
            return response

        response.headers["X-Frame-Options"] = "DENY"

        # Sanitize and validate X-XSS-Protection
        xxspp = request.headers.get("X-XSS-Protection", "")
        if not re.match(r"^[^;]+(?:;[^;]+)*$", xxspp):
            logger.error(
                "Invalid X-XSS-Protection header",
                request_id=request.state.request_id,
                client_ip=request.client.host if request.client else "unknown",
            )
            return response

        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Sanitize and validate Referrer-Policy
        rrp = request.headers.get("Referrer-Policy", "")
        if not re.match(r"^[^;]+(?:;[^;]+)*$", rrp):
            logger.error(
                "Invalid Referrer-Policy header",
                request_id=request.state.request_id,
                client_ip=request.client.host if request.client else "unknown",
            )
            return response

        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Sanitize and validate Permissions-Policy
        pp = request.headers.get("Permissions-Policy", "")
        if not re.match(r"^[^;]+(?:;[^;]+)*$", pp):
            logger.error(
                "Invalid Permissions-Policy header",
                request_id=request.state.request_id,
                client_ip=request.client.host if request.client else "unknown",
            )
            return response

        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=()"
        )

        return response


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Add unique request ID for tracing."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Response]
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
        self, request: Request, call_next: Callable[[Request], Response]
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