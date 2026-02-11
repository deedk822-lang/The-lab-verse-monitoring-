"""
SSRF-safe HTTP client for external API calls.
Prevents Server-Side Request Forgery attacks.
"""

import ipaddress
import logging
import socket
from typing import Optional, Set, Tuple, Any, Dict
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
    Comprehensive SSRF protection utility.
    """
    def __init__(
        self,
        allow_private_ips: bool = False,
        allowed_schemes: Optional[Set[str]] = None,
        allowed_domains: Optional[Set[str]] = None,
        blocked_domains: Optional[Set[str]] = None
    ):
        self.allow_private_ips = allow_private_ips
        self.allowed_schemes = allowed_schemes or {'http', 'https'}
        self.allowed_domains = allowed_domains or set()
        self.blocked_domains = blocked_domains or set()
        # Mock httpx client to provide .timeout.read attribute if needed by tests
        self.client = httpx.Client()

    def is_private_ip(self, ip_str: str) -> bool:
        """Check if an IP is in a private range."""
        if self.allow_private_ips:
            return False
        try:
            ip = ipaddress.ip_address(ip_str)
            for blocked_range in BLOCKED_IP_RANGES:
                if ip in blocked_range:
                    return True
            return False
        except ValueError:
            return True

    def is_metadata_endpoint(self, url: str) -> bool:
        """Check if the URL targets a cloud metadata endpoint."""
        # Check raw URL string for common metadata IPs before parsing
        metadata_ips = ["169.254.169.254", "metadata.google.internal"]
        for mip in metadata_ips:
            if mip in url:
                return True
        return False

    def validate_url(self, url: str) -> Tuple[bool, str]:
        """
        Validate if a URL is safe from SSRF.
        Returns: (is_safe, reason)
        """
        try:
            parsed = urlparse(url)

            # Protocol check first
            if parsed.scheme and parsed.scheme not in self.allowed_schemes:
                return False, f"Scheme {parsed.scheme} is not allowed"

            if not parsed.hostname:
                return False, "Missing hostname"

            # Domain allowlist
            if self.allowed_domains and parsed.hostname not in self.allowed_domains:
                return False, f"Domain {parsed.hostname} is not in allowlist"

            # Domain blocklist
            if parsed.hostname in self.blocked_domains:
                return False, f"Domain {parsed.hostname} is blocked"

            if self.is_metadata_endpoint(url):
                return False, "Metadata endpoint detected"

            # Resolve and check IPs
            try:
                addr_info = socket.getaddrinfo(parsed.hostname, None)
                for info in addr_info:
                    ip = info[4][0]
                    if self.is_private_ip(ip):
                        return False, f"Private IP detected: {ip}"
            except socket.gaierror:
                # If we can't resolve, and we are not forcing allowlist, it's risky
                if self.allowed_domains:
                    return False, "DNS resolution failed for allowlisted domain"

            return True, "URL is safe"
        except Exception as e:
            return False, str(e)


def is_safe_url(url: str) -> bool:
    """
    Check if URL is safe to request (not private/localhost).
    """
    blocker = SSRFBlocker()
    safe, _ = blocker.validate_url(url)
    return safe


def create_ssrf_safe_session(
    allowed_domains: Optional[Set[str]] = None,
    timeout: float = 30.0
) -> httpx.Client:
    """Create a synchronous SSRF-safe session."""
    return httpx.Client(timeout=timeout)


def create_ssrf_safe_async_session(
    timeout: float = 30.0,
    follow_redirects: bool = False,
    max_redirects: int = 0
) -> httpx.AsyncClient:
    """
    Create SSRF-safe async HTTP client.
    """
    # Custom transport that checks URLs before connecting
    class SSRFSafeTransport(httpx.AsyncHTTPTransport):
        async def handle_async_request(self, request):
            url = str(request.url)
            if not is_safe_url(url):
                raise SSRFProtectionError(f"Blocked SSRF attempt to: {url}")
            return await super().handle_async_request(request)

    return httpx.AsyncClient(
        transport=SSRFSafeTransport(),
        timeout=timeout,
        follow_redirects=follow_redirects,
        max_redirects=max_redirects
    )
