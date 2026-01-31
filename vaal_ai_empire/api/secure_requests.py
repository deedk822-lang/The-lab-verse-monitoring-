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


class SSRFBlocker:
    """Validator for URLs to prevent SSRF attacks."""

    def __init__(
        self,
        allow_private_ips: bool = False,
        allowed_domains: Optional[Set[str]] = None,
        blocked_domains: Optional[Set[str]] = None,
        allowed_schemes: Optional[Set[str]] = None
    ):
        self.allow_private_ips = allow_private_ips
        self.allowed_domains = allowed_domains
        self.blocked_domains = blocked_domains
        self.allowed_schemes = allowed_schemes or {'http', 'https'}

    def is_private_ip(self, ip_str: str) -> bool:
        """Check if IP address is private/local."""
        try:
            ip = ipaddress.ip_address(ip_str)
            return any(ip in net for net in BLOCKED_IP_RANGES)
        except ValueError:
            return False

    def is_metadata_endpoint(self, hostname: str) -> bool:
        """Check if hostname is a known cloud metadata endpoint."""
        metadata_hosts = {
            '169.254.169.254',
            'metadata.google.internal',
            'instance-data',
            '100.100.100.200'  # Alibaba Cloud
        }
        return hostname.lower() in metadata_hosts

    def validate_url(self, url: str) -> Tuple[bool, str]:
        """
        Validate URL for security.

        Returns:
            (is_valid, error_message)
        """
        try:
            parsed = urlparse(url)

            if not parsed.scheme or parsed.scheme not in self.allowed_schemes:
                return False, f"Scheme {parsed.scheme} is not allowed"

            if not parsed.hostname:
                return False, "URL has no hostname"

            # Domain blocklist
            if self.blocked_domains and parsed.hostname.lower() in self.blocked_domains:
                return False, f"Domain {parsed.hostname} is blocked"

            # Domain allowlist
            if self.allowed_domains and parsed.hostname.lower() not in self.allowed_domains:
                return False, f"Domain {parsed.hostname} is not in allowlist"

            # Metadata protection
            if self.is_metadata_endpoint(parsed.hostname):
                return False, "Access to metadata endpoints is blocked"

            # DNS resolution and IP check
            try:
                # Use getaddrinfo to handle IPv4/IPv6 and prevent some rebinding
                addr_info = socket.getaddrinfo(parsed.hostname, parsed.port or 80)
                for item in addr_info:
                    ip_str = item[4][0]
                    if not self.allow_private_ips and self.is_private_ip(ip_str):
                        return False, f"URL resolves to private IP: {ip_str}"
            except socket.gaierror:
                return False, f"Could not resolve hostname: {parsed.hostname}"

            return True, ""

        except Exception as e:
            return False, f"Validation error: {str(e)}"


def is_safe_url(url: str) -> bool:
    """Check if URL is safe to request."""
    blocker = SSRFBlocker()
    valid, _ = blocker.validate_url(url)
    return valid


def create_ssrf_safe_session(
    allowed_domains: Optional[Set[str]] = None,
    timeout: float = 30.0,
    **kwargs
) -> httpx.Client:
    """Create SSRF-safe synchronous HTTP client."""

    blocker = SSRFBlocker(allowed_domains=allowed_domains)

    class SSRFSafeTransport(httpx.HTTPTransport):
        def handle_request(self, request):
            url = str(request.url)
            valid, error = blocker.validate_url(url)
            if not valid:
                raise ValueError(f"Blocked SSRF attempt: {error}")
            return super().handle_request(request)

    return httpx.Client(
        transport=SSRFSafeTransport(),
        timeout=timeout,
        **kwargs
    )


def create_ssrf_safe_async_session(
    timeout: float = 30.0,
    follow_redirects: bool = False,
    max_redirects: int = 0
) -> httpx.AsyncClient:
    """Create SSRF-safe async HTTP client."""

    blocker = SSRFBlocker()

    class SSRFSafeAsyncTransport(httpx.AsyncHTTPTransport):
        async def handle_async_request(self, request):
            url = str(request.url)
            valid, error = blocker.validate_url(url)
            if not valid:
                raise ValueError(f"Blocked SSRF attempt: {error}")
            return await super().handle_async_request(request)

    return httpx.AsyncClient(
        transport=SSRFSafeAsyncTransport(),
        timeout=timeout,
        follow_redirects=follow_redirects,
        max_redirects=max_redirects,
        headers={
            'User-Agent': 'VAAL-AI-Empire/1.0'
        }
    )
