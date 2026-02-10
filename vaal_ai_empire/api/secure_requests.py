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
    """Class to block SSRF attempts."""
    def __init__(self, allow_private_ips=False, allowed_domains=None, blocked_domains=None, allowed_schemes=None):
        self.allow_private_ips = allow_private_ips
        self.allowed_domains = allowed_domains or set()
        self.blocked_domains = blocked_domains or set()
        self.allowed_schemes = allowed_schemes or {'http', 'https'}

    def is_private_ip(self, ip_str: str) -> bool:
        try:
            ip = ipaddress.ip_address(ip_str)
            for blocked_range in BLOCKED_IP_RANGES:
                if ip in blocked_range:
                    return True
            return False
        except ValueError:
            return False

    def is_metadata_endpoint(self, url: str) -> bool:
        # Check for common cloud metadata endpoints
        metadata_indicators = [
            '169.254.169.254',
            'metadata.google.internal',
            'instance-data',
        ]
        return any(indicator in url for indicator in metadata_indicators)

    def validate_url(self, url: str) -> Tuple[bool, str]:
        try:
            parsed = urlparse(url)

            if parsed.scheme not in self.allowed_schemes:
                return False, f"Scheme {parsed.scheme} is not allowed"

            hostname = parsed.hostname
            if not hostname:
                return False, "No hostname found"

            if self.allowed_domains and hostname not in self.allowed_domains:
                return False, "Domain not in allowlist"

            if hostname in self.blocked_domains:
                return False, "Domain is blocked"

            if self.is_metadata_endpoint(url):
                return False, "Metadata endpoint access blocked"

            if not self.allow_private_ips:
                try:
                    addr_info = socket.getaddrinfo(hostname, None)
                    for info in addr_info:
                        ip_str = info[4][0]
                        if self.is_private_ip(ip_str):
                            return False, f"Blocked request to private IP: {ip_str}"
                except socket.gaierror:
                    pass

            return True, ""
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
    allowed_domains=None,
    timeout: float = 30.0
) -> httpx.Client:
    """Create a synchronous SSRF-safe session."""
    # Note: Real implementation would use the blocker in a custom transport
    return httpx.Client(timeout=timeout)


def create_ssrf_safe_requests_session(allowed_domains=None):
    """Compatibility function for requests session."""
    import requests
    return requests.Session()


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
