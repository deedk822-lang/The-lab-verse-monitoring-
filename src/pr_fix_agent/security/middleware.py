"""
Security Headers Middleware - Global Production Standard (S4)
Implements: CSP, HSTS, X-Frame-Options, etc.
"""

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware that adds production-grade security headers to all responses.

    ✅ S4: CSP, HSTS, X-Frame-Options, X-Content-Type-Options
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        response = await call_next(request)

        # 1. Strict-Transport-Security (HSTS)
        # 1 year max-age, include subdomains, allow preloading
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains; preload"
        )

        # 2. Content-Security-Policy (CSP)
        # Tight default-src 'self', restricted scripts/styles
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )

        # 3. X-Content-Type-Options
        # Prevent MIME-type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # 4. X-Frame-Options
        # Prevent Clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # 5. X-XSS-Protection
        # Legacy XSS filter enablement
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # 6. Referrer-Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # 7. Permissions-Policy
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=()"
        )

        return response
