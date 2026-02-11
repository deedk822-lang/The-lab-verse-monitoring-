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
    """Blocker for SSRF attempts."""

    def __init__(
        self,
        allow_private_ips: bool = False,
        allowed_schemes: Optional[Set[str]] = None,
        allowed_domains: Optional[Set[str]] = None,
        blocked_domains: Optional[Set[str]] = None,
    ):
        self.allow_private_ips = allow_private_ips
        self.allowed_schemes = allowed_schemes or {'http', 'https'}
        self.allowed_domains = allowed_domains
        self.blocked_domains = blocked_domains

    def is_private_ip(self, ip_str: str) -> bool:
        """Check if an IP address is private/internal."""
        try:
            ip = ipaddress.ip_address(ip_str)
            return any(ip in net for net in BLOCKED_IP_RANGES)
        except ValueError:
            return False

    def is_metadata_endpoint(self, hostname: str) -> bool:
        """Check if hostname/IP is a cloud metadata endpoint."""
        metadata_hosts = {'169.254.169.254', 'metadata.google.internal', 'instance-data'}
        return hostname in metadata_hosts

    def validate_url(self, url: str) -> Tuple[bool, str]:
        """
        Validate URL for SSRF protection.

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            parsed = urlparse(url)

            # Scheme check
            if parsed.scheme not in self.allowed_schemes:
                return False, f"Scheme {parsed.scheme} is not allowed"

            hostname = parsed.hostname
            if not hostname:
                return False, "No hostname found in URL"

            # Metadata check
            if self.is_metadata_endpoint(hostname):
                return False, "Access to metadata endpoint is blocked"

            # Domain allowlist
            if self.allowed_domains and hostname not in self.allowed_domains:
                return False, f"Domain {hostname} is not in allowlist"

            # Domain blocklist
            if self.blocked_domains and hostname in self.blocked_domains:
                return False, f"Domain {hostname} is blocked"

            # DNS Resolution & Private IP check
            if not self.allow_private_ips:
                try:
                    addr_info = socket.getaddrinfo(hostname, None)
                    for info in addr_info:
                        ip_str = info[4][0]
                        if self.is_private_ip(ip_str):
                            return False, f"Domain {hostname} resolved to private IP {ip_str}"
                except socket.gaierror:
                    # Allow if can't resolve (e.g. invalid domain but not explicitly blocked)
                    pass

            return True, ""
        except Exception as e:
            return False, str(e)


def is_safe_url(url: str) -> bool:
    """
    Check if URL is safe to request (not private/localhost).
    
    Args:
        url: URL to check
        
    Returns:
        True if safe, False otherwise
    """
    try:
        parsed = urlparse(url)

        # Must have a hostname
        if not parsed.hostname:
            logger.warning(f"URL has no hostname: {url}")
            return False

        # Protocol check
        if parsed.scheme not in ('http', 'https'):
            logger.error(f"Blocked request with unsupported scheme: {parsed.scheme}")
            return False

        # Resolve hostname to IP
        hostname = parsed.hostname
        try:
            addr_info = socket.getaddrinfo(hostname, None)
            for info in addr_info:
                ip_str = info[4][0]
                ip = ipaddress.ip_address(ip_str)
                # Check if IP is in blocked ranges
                for blocked_range in BLOCKED_IP_RANGES:
                    if ip in blocked_range:
                        logger.error(
                            f"Blocked request to private IP: {ip} "
                            f"(range: {blocked_range}) for URL: {url}"
                        )
                        return False
        except socket.gaierror:
            # If we can't resolve, we might want to block or allow depending on policy.
            # For strictness, let's allow it if it's not explicitly blocked by name.
            pass

        return True

    except Exception as e:
        logger.error(f"Error checking URL safety: {e}")
        return False


def create_ssrf_safe_session(
    allowed_domains: Optional[Set[str]] = None,
    timeout: float = 30.0
) -> httpx.Client:
    """Create a synchronous SSRF-safe session."""
    blocker = SSRFBlocker(allowed_domains=allowed_domains)

    class SSRFSafeTransport(httpx.HTTPTransport):
        def handle_request(self, request: httpx.Request) -> httpx.Response:
            url = str(request.url)
            valid, error = blocker.validate_url(url)
            if not valid:
                raise SSRFProtectionError(f"Blocked SSRF attempt: {error}")
            return super().handle_request(request)

    return httpx.Client(transport=SSRFSafeTransport(), timeout=timeout)


def create_ssrf_safe_async_session(
    timeout: float = 30.0,
    follow_redirects: bool = False,
    max_redirects: int = 0
) -> httpx.AsyncClient:
    """
    Create SSRF-safe async HTTP client.

    Args:
        timeout: Request timeout in seconds
        follow_redirects: Whether to follow redirects
        max_redirects: Maximum number of redirects

    Returns:
        Configured async HTTP client
    """
    blocker = SSRFBlocker()

    # Custom transport that checks URLs before connecting
    class SSRFSafeTransport(httpx.AsyncHTTPTransport):
        async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
            url = str(request.url)
            valid, error = blocker.validate_url(url)
            if not valid:
                raise SSRFProtectionError(f"Blocked SSRF attempt: {error}")
            return await super().handle_async_request(request)

    return httpx.AsyncClient(
        transport=SSRFSafeTransport(),
        timeout=timeout,
        follow_redirects=follow_redirects,
        max_redirects=max_redirects
    )
