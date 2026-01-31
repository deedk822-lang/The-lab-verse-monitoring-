from __future__ import annotations

import ipaddress
import socket
from typing import Any, Union
from urllib.parse import urlparse

import httpx
import requests
from requests.adapters import HTTPAdapter


class SSRFBlocker:
    """
    SSRF (Server-Side Request Forgery) protection.

    Blocks requests to:
    - Private IP ranges (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16)
    - Localhost (127.0.0.0/8, ::1)
    - Link-local addresses (169.254.0.0/16, fe80::/10)
    - Metadata services (169.254.169.254)
    """

    def __init__(self, allowed_domains: set[str] | None = None):
        """
        Initialize SSRF blocker.

        Args:
            allowed_domains: Set of domains to allow (if None, block all private IPs)
        """
        self.allowed_domains = allowed_domains or set()

        # Private IP ranges to block
        self.blocked_networks = [
            ipaddress.ip_network("10.0.0.0/8"),      # Private
            ipaddress.ip_network("172.16.0.0/12"),   # Private
            ipaddress.ip_network("192.168.0.0/16"),  # Private
            ipaddress.ip_network("127.0.0.0/8"),     # Localhost
            ipaddress.ip_network("169.254.0.0/16"),  # Link-local
            ipaddress.ip_network("::1/128"),         # IPv6 localhost
            ipaddress.ip_network("fe80::/10"),       # IPv6 link-local
            ipaddress.ip_network("fc00::/7"),        # IPv6 unique local
        ]

    def is_safe_url(self, url: str) -> tuple[bool, str]:
        """
        Check if URL is safe from SSRF.

        Args:
            url: URL to check

        Returns:
            (is_safe, reason) tuple
        """
        try:
            parsed = urlparse(url)
            hostname = parsed.hostname

            if not hostname:
                return False, "No hostname in URL"

            # Check if domain is explicitly allowed
            if hostname in self.allowed_domains:
                return True, "Domain in allowed list"

            # Resolve hostname to IP
            try:
                ip_str = socket.gethostbyname(hostname)
                ip = ipaddress.ip_address(ip_str)
            except (socket.gaierror, ValueError) as e:
                return False, f"Cannot resolve hostname: {e}"

            # Check if IP is in blocked networks
            for network in self.blocked_networks:
                if ip in network:
                    return False, f"IP {ip} is in blocked network {network}"

            return True, "URL is safe"

        except Exception as e:
            return False, f"Error validating URL: {e}"

    def validate_request(self, request: Union[httpx.Request, requests.PreparedRequest]) -> None:
        """
        Validate request before sending.

        Args:
            request: httpx.Request or requests.PreparedRequest to validate

        Raises:
            ValueError: If request is blocked
        """
        url = str(request.url)
        is_safe, reason = self.is_safe_url(url)

        if not is_safe:
            raise ValueError(f"SSRF protection: Blocked request to {url}. Reason: {reason}")


# --- HTTPX Integration ---

class SSRFBlockerTransport(httpx.HTTPTransport):
    """Custom transport that applies SSRF protection for HTTPX."""

    def __init__(self, blocker: SSRFBlocker, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.blocker = blocker

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        self.blocker.validate_request(request)
        return super().handle_request(request)


class SSRFBlockerAsyncTransport(httpx.AsyncHTTPTransport):
    """Async custom transport that applies SSRF protection for HTTPX."""

    def __init__(self, blocker: SSRFBlocker, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.blocker = blocker

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        self.blocker.validate_request(request)
        return await super().handle_async_request(request)


def create_ssrf_safe_session(allowed_domains: set[str] | None = None, timeout: float = 30.0) -> httpx.Client:
    blocker = SSRFBlocker(allowed_domains=allowed_domains)
    transport = SSRFBlockerTransport(blocker=blocker)
    return httpx.Client(transport=transport, timeout=timeout)


def create_ssrf_safe_async_session(allowed_domains: set[str] | None = None, timeout: float = 30.0) -> httpx.AsyncClient:
    blocker = SSRFBlocker(allowed_domains=allowed_domains)
    transport = SSRFBlockerAsyncTransport(blocker=blocker)
    return httpx.AsyncClient(transport=transport, timeout=timeout)


# --- Requests Integration ---

class SSRFSafeAdapter(HTTPAdapter):
    """Custom adapter that applies SSRF protection for Requests."""

    def __init__(self, blocker: SSRFBlocker, *args: Any, **kwargs: Any):
        self.blocker = blocker
        super().__init__(*args, **kwargs)

    def send(self, request: requests.PreparedRequest, **kwargs: Any) -> requests.Response:
        self.blocker.validate_request(request)
        return super().send(request, **kwargs)


def create_ssrf_safe_requests_session(allowed_domains: set[str] | None = None) -> requests.Session:
    """Create a SSRF-safe requests Session."""
    blocker = SSRFBlocker(allowed_domains=allowed_domains)
    session = requests.Session()
    adapter = SSRFSafeAdapter(blocker)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session
