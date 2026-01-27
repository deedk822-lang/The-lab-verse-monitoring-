"""
SSRF (Server-Side Request Forgery) protection for external requests.
Implements allow/deny lists and validates URLs before making requests.
"""

import ipaddress
import socket
import logging
from typing import Optional, Set, List
from urllib.parse import urlparse
import httpx

logger = logging.getLogger(__name__)

# Private IP ranges (RFC 1918, RFC 4193, etc.)
PRIVATE_IP_RANGES = [
    ipaddress.ip_network('10.0.0.0/8'),
    ipaddress.ip_network('172.16.0.0/12'),
    ipaddress.ip_network('192.168.0.0/16'),
    ipaddress.ip_network('127.0.0.0/8'),
    ipaddress.ip_network('169.254.0.0/16'),  # Link-local
    ipaddress.ip_network('::1/128'),  # IPv6 loopback
    ipaddress.ip_network('fc00::/7'),  # IPv6 private
    ipaddress.ip_network('fe80::/10'),  # IPv6 link-local
]

# Cloud metadata endpoints
METADATA_ENDPOINTS = [
    '169.254.169.254',  # AWS, Azure, GCP
    '169.254.170.2',    # ECS task metadata
    'metadata.google.internal',
]

# Default allowed schemes
ALLOWED_SCHEMES = {'http', 'https'}

# Default timeout
DEFAULT_TIMEOUT = 30.0


class SSRFBlocker:
    """
    SSRF protection validator for URLs and requests.
    """

    def __init__(
        self,
        allowed_domains: Optional[Set[str]] = None,
        blocked_domains: Optional[Set[str]] = None,
        allow_private_ips: bool = False,
        allowed_schemes: Optional[Set[str]] = None,
        max_redirects: int = 3
    ):
        """
        Initialize SSRF blocker.

        Args:
            allowed_domains: Whitelist of allowed domains (if None, all allowed except blocked)
            blocked_domains: Blacklist of blocked domains
            allow_private_ips: Whether to allow requests to private IP ranges
            allowed_schemes: Allowed URL schemes (default: http, https)
            max_redirects: Maximum number of redirects to follow
        """
        self.allowed_domains = allowed_domains or set()
        self.blocked_domains = blocked_domains or set()
        self.allow_private_ips = allow_private_ips
        self.allowed_schemes = allowed_schemes or ALLOWED_SCHEMES
        self.max_redirects = max_redirects

    def is_private_ip(self, ip_str: str) -> bool:
        """Check if IP address is in private range."""
        try:
            ip = ipaddress.ip_address(ip_str)
            return any(ip in network for network in PRIVATE_IP_RANGES)
        except ValueError:
            return False

    def is_metadata_endpoint(self, hostname: str) -> bool:
        """Check if hostname is a cloud metadata endpoint."""
        return hostname in METADATA_ENDPOINTS

    def resolve_hostname(self, hostname: str) -> List[str]:
        """Resolve hostname to IP addresses."""
        try:
            addr_info = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
            return list(set(info[4][0] for info in addr_info))
        except socket.gaierror as e:
            logger.warning(f"Failed to resolve hostname {hostname}: {e}")
            return []

    def validate_url(self, url: str) -> tuple[bool, Optional[str]]:
        """
        Validate URL for SSRF vulnerabilities.

        Returns:
            (is_valid, error_message)
        """
        try:
            parsed = urlparse(url)
        except Exception as e:
            return False, f"Invalid URL format: {e}"

        # Check scheme
        if parsed.scheme not in self.allowed_schemes:
            return False, f"Scheme '{parsed.scheme}' not allowed"

        hostname = parsed.hostname
        if not hostname:
            return False, "URL must have a hostname"

        # Check for metadata endpoints
        if self.is_metadata_endpoint(hostname):
            return False, "Access to cloud metadata endpoints is blocked"

        # Check domain allowlist/blocklist
        if self.blocked_domains and hostname in self.blocked_domains:
            return False, f"Domain '{hostname}' is blocked"

        if self.allowed_domains and hostname not in self.allowed_domains:
            return False, f"Domain '{hostname}' not in allowlist"

        # Resolve hostname to IPs
        ip_addresses = self.resolve_hostname(hostname)

        if not ip_addresses:
            return False, f"Could not resolve hostname '{hostname}'"

        # Check for private IPs
        if not self.allow_private_ips:
            for ip in ip_addresses:
                if self.is_private_ip(ip):
                    return False, f"Access to private IP '{ip}' is blocked"

        return True, None

    def validate_and_raise(self, url: str):
        """Validate URL and raise exception if invalid."""
        is_valid, error = self.validate_url(url)
        if not is_valid:
            raise SSRFProtectionError(error)


class SSRFProtectionError(Exception):
    """Raised when SSRF protection blocks a request."""
    pass


def create_ssrf_safe_session(
    allowed_domains: Optional[Set[str]] = None,
    blocked_domains: Optional[Set[str]] = None,
    allow_private_ips: bool = False,
    timeout: float = DEFAULT_TIMEOUT,
    max_redirects: int = 3
) -> httpx.Client:
    """
    Create an SSRF-protected HTTP client session.

    Args:
        allowed_domains: Whitelist of allowed domains
        blocked_domains: Blacklist of blocked domains
        allow_private_ips: Whether to allow private IP addresses
        timeout: Request timeout in seconds
        max_redirects: Maximum redirects to follow

    Returns:
        SSRF-protected httpx.Client
    """
    blocker = SSRFBlocker(
        allowed_domains=allowed_domains,
        blocked_domains=blocked_domains,
        allow_private_ips=allow_private_ips,
        max_redirects=max_redirects
    )

    class SSRFSafeTransport(httpx.HTTPTransport):
        """Custom transport that validates URLs before requests."""

        def handle_request(self, request: httpx.Request) -> httpx.Response:
            url = str(request.url)
            blocker.validate_and_raise(url)
            return super().handle_request(request)

    return httpx.Client(
        transport=SSRFSafeTransport(),
        timeout=httpx.Timeout(timeout),
        follow_redirects=True,
        max_redirects=max_redirects,
        verify=True  # Always verify SSL
    )


async def create_ssrf_safe_async_session(
    allowed_domains: Optional[Set[str]] = None,
    blocked_domains: Optional[Set[str]] = None,
    allow_private_ips: bool = False,
    timeout: float = DEFAULT_TIMEOUT,
    max_redirects: int = 3
) -> httpx.AsyncClient:
    """
    Create an SSRF-protected async HTTP client session.

    Args:
        allowed_domains: Whitelist of allowed domains
        blocked_domains: Blacklist of blocked domains
        allow_private_ips: Whether to allow private IP addresses
        timeout: Request timeout in seconds
        max_redirects: Maximum redirects to follow

    Returns:
        SSRF-protected httpx.AsyncClient
    """
    blocker = SSRFBlocker(
        allowed_domains=allowed_domains,
        blocked_domains=blocked_domains,
        allow_private_ips=allow_private_ips,
        max_redirects=max_redirects
    )

    class SSRFSafeAsyncTransport(httpx.AsyncHTTPTransport):
        """Custom async transport that validates URLs before requests."""

        async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
            url = str(request.url)
            blocker.validate_and_raise(url)
            return await super().handle_async_request(request)

    return httpx.AsyncClient(
        transport=SSRFSafeAsyncTransport(),
        timeout=httpx.Timeout(timeout),
        follow_redirects=True,
        max_redirects=max_redirects,
        verify=True  # Always verify SSL
    )


# Convenience wrappers
def safe_get(url: str, **kwargs) -> httpx.Response:
    """Make SSRF-safe GET request."""
    with create_ssrf_safe_session() as client:
        return client.get(url, **kwargs)


def safe_post(url: str, **kwargs) -> httpx.Response:
    """Make SSRF-safe POST request."""
    with create_ssrf_safe_session() as client:
        return client.post(url, **kwargs)


async def safe_get_async(url: str, **kwargs) -> httpx.Response:
    """Make SSRF-safe async GET request."""
    async with create_ssrf_safe_async_session() as client:
        return await client.get(url, **kwargs)


async def safe_post_async(url: str, **kwargs) -> httpx.Response:
    """Make SSRF-safe async POST request."""
    async with create_ssrf_safe_async_session() as client:
        return await client.post(url, **kwargs)
