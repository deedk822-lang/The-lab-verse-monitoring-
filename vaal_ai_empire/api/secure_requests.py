"""
SSRF-safe HTTP client for external API calls.
Prevents Server-Side Request Forgery attacks.
"""

import ipaddress
import logging
import socket
from typing import Optional, Set, Tuple
from urllib.parse import urlparse

import httpx

logger = logging.getLogger(__name__)

# Blocked IP ranges (private networks, localhost, etc.)
BLOCKED_IP_RANGES = [
    ipaddress.ip_network('0.0.0.0/8'),
    ipaddress.ip_network('10.0.0.0/8'),
    ipaddress.ip_network('127.0.0.0/8'),
    ipaddress.ip_network('169.254.0.0/16'),
    ipaddress.ip_network('172.16.0.0/12'),
    ipaddress.ip_network('192.168.0.0/16'),
    ipaddress.ip_network('224.0.0.0/4'),
    ipaddress.ip_network('240.0.0.0/4'),
    ipaddress.ip_network('::1/128'),
    ipaddress.ip_network('fe80::/10'),
    ipaddress.ip_network('fc00::/7'),
]


class SSRFProtectionError(Exception):
    """Raised when an SSRF attempt is detected."""
    pass


class SSRFBlocker:
    """
    SSRF (Server-Side Request Forgery) protection.
    Blocks requests to private IPs, metadata endpoints, and non-allowlisted domains.
    """

    def __init__(
        self,
        allowed_domains: Optional[Set[str]] = None,
        blocked_domains: Optional[Set[str]] = None,
        allowed_schemes: Optional[Set[str]] = None,
        allow_private_ips: bool = False
    ):
        self.allowed_domains = allowed_domains or set()
        self.blocked_domains = blocked_domains or set()
        self.allowed_schemes = allowed_schemes or {'http', 'https'}
        self.allow_private_ips = allow_private_ips

    def is_private_ip(self, ip_str: str) -> bool:
        """Check if an IP address is in a blocked private range."""
        try:
            ip = ipaddress.ip_address(ip_str)
            for blocked_range in BLOCKED_IP_RANGES:
                if ip in blocked_range:
                    return True
            return False
        except ValueError:
            return False

    def is_metadata_endpoint(self, hostname: str) -> bool:
        """Check if hostname is a known cloud metadata endpoint."""
        metadata_hosts = {
            "169.254.169.254",
            "metadata.google.internal",
            "metadata",
            "instance-data"
        }
        return hostname.lower() in metadata_hosts or "metadata.google.internal" in hostname.lower()

    def validate_url(self, url: str) -> Tuple[bool, str]:
        """
        Validate if a URL is safe to request.
        Returns (is_safe, reason).
        """
        try:
            parsed = urlparse(url)

            # Scheme validation
            if parsed.scheme not in self.allowed_schemes:
                return False, f"Scheme '{parsed.scheme}' is not allowed"

            hostname = parsed.hostname
            if not hostname:
                return False, "URL has no hostname"

            # Blocklist validation
            if hostname.lower() in [d.lower() for d in self.blocked_domains]:
                return False, f"Domain '{hostname}' is explicitly blocked"

            # Allowlist validation
            if self.allowed_domains and hostname.lower() not in [d.lower() for d in self.allowed_domains]:
                return False, f"Domain '{hostname}' is not in allowlist"

            # Metadata endpoint validation
            if self.is_metadata_endpoint(hostname):
                return False, f"Access to metadata endpoint '{hostname}' is blocked"

            # IP validation
            if not self.allow_private_ips:
                try:
                    # DNS Rebinding protection: resolve and check IP
                    addr_info = socket.getaddrinfo(hostname, None)
                    for info in addr_info:
                        ip_str = info[4][0]
                        if self.is_private_ip(ip_str):
                            return False, f"Blocked request to private IP: {ip_str}"
                except socket.gaierror:
                    # Allow if can't resolve (e.g. invalid domain but passed other checks)
                    pass

            return True, ""

        except Exception as e:
            return False, f"Validation error: {str(e)}"


def is_safe_url(url: str) -> bool:
    """Legacy compatibility wrapper for is_safe_url."""
    blocker = SSRFBlocker()
    safe, _ = blocker.validate_url(url)
    return safe


def create_ssrf_safe_session(
    allowed_domains: Optional[Set[str]] = None,
    timeout: float = 30.0
) -> httpx.Client:
    """Create a synchronous SSRF-safe session."""
    blocker = SSRFBlocker(allowed_domains=allowed_domains)

    class SSRFSafeTransport(httpx.HTTPTransport):
        def handle_request(self, request: httpx.Request) -> httpx.Response:
            url = str(request.url)
            safe, reason = blocker.validate_url(url)
            if not safe:
                raise SSRFProtectionError(f"Blocked SSRF attempt: {reason}")
            return super().handle_request(request)

    return httpx.Client(transport=SSRFSafeTransport(), timeout=timeout)


def create_ssrf_safe_async_session(
    allowed_domains: Optional[Set[str]] = None,
    timeout: float = 30.0,
    follow_redirects: bool = False,
    max_redirects: int = 0
) -> httpx.AsyncClient:
    """Create SSRF-safe async HTTP client."""
    blocker = SSRFBlocker(allowed_domains=allowed_domains)

    class SSRFSafeTransport(httpx.AsyncHTTPTransport):
        async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
            url = str(request.url)
            safe, reason = blocker.validate_url(url)
            if not safe:
                raise SSRFProtectionError(f"Blocked SSRF attempt: {reason}")
            return await super().handle_async_request(request)

    return httpx.AsyncClient(
        transport=SSRFSafeTransport(),
        timeout=timeout,
        follow_redirects=follow_redirects,
        max_redirects=max_redirects
    )
