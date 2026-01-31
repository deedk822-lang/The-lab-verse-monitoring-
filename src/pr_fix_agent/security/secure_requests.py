"""
SSRF Protection - Global Production Standard (Fix #6)
Blocks internal/private IP probing using custom httpx transport.
"""

import socket
import ipaddress
from typing import Any, Set, Optional, Union

import httpx
import structlog

logger = structlog.get_logger()


class SSRFBlocker:
    """
    Validates requests to prevent SSRF (Server-Side Request Forgery).

    Blocks:
    - 127.0.0.1 / localhost
    - Private IP ranges (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16)
    - Metadata services (169.254.169.254)
    - IPv6 loopback (::1)
    """

    def __init__(self, allowed_domains: Optional[Set[str]] = None):
        self.allowed_domains = allowed_domains or set()

    def validate_request(self, request: httpx.Request) -> None:
        """Validate request target before sending."""
        url = request.url
        host = url.host

        # 1. Allow if in explicit allowlist
        if host in self.allowed_domains:
            return

        # 2. Resolve hostname to IP
        try:
            ip_addr = socket.gethostbyname(host)
            ip = ipaddress.ip_address(ip_addr)
        except Exception as e:
            logger.warning("ssrf_resolution_failed", host=host, error=str(e))
            # If we can't resolve it, it might be dangerous
            raise ValueError(f"SSRF protection: Could not resolve host {host}")

        # 3. Check if IP is private or loopback
        if ip.is_loopback:
            raise ValueError(f"SSRF protection: Loopback address blocked: {ip}")

        if ip.is_private:
            raise ValueError(f"SSRF protection: Private IP address blocked: {ip}")

        if ip.is_link_local:
            raise ValueError(f"SSRF protection: Link-local address blocked: {ip}")


class SSRFBlockerTransport(httpx.HTTPTransport):
    """Custom transport that validates requests for SSRF."""

    def __init__(self, blocker: SSRFBlocker, **kwargs: Any):
        super().__init__(**kwargs)
        self.blocker = blocker

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        self.blocker.validate_request(request)
        return super().handle_request(request)


class SSRFBlockerAsyncTransport(httpx.AsyncHTTPTransport):
    """Custom async transport that validates requests for SSRF."""

    def __init__(self, blocker: SSRFBlocker, **kwargs: Any):
        super().__init__(**kwargs)
        self.blocker = blocker

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        self.blocker.validate_request(request)
        return await super().handle_async_request(request)


def create_ssrf_safe_session(
    allowed_domains: Optional[Set[str]] = None,
    is_async: bool = False
) -> Union[httpx.Client, httpx.AsyncClient]:
    """
    Create a production-safe HTTP client with SSRF protection.

    ✅ FIX: Actually applies the SSRFBlocker via custom transport
    """
    blocker = SSRFBlocker(allowed_domains=allowed_domains)

    if is_async:
        transport: SSRFBlockerAsyncTransport = SSRFBlockerAsyncTransport(blocker=blocker)
        return httpx.AsyncClient(transport=transport)
    else:
        sync_transport: SSRFBlockerTransport = SSRFBlockerTransport(blocker=blocker)
        return httpx.Client(transport=sync_transport)
