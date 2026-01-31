"""
SSRF-safe HTTP client for external API calls.
Prevents Server-Side Request Forgery attacks.
"""

import ipaddress
import logging
<<<<<<< HEAD
from typing import Optional, Set, Tuple
import httpx
=======
import socket
>>>>>>> main
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


<<<<<<< HEAD
class SSRFProtectionError(Exception):
    """Raised when an SSRF attempt is detected."""
    pass


class SSRFBlocker:
    """Validator for URLs to prevent SSRF."""

    def __init__(
        self,
        allow_private_ips: bool = False,
        allowed_schemes: Optional[Set[str]] = None,
        allowed_domains: Optional[Set[str]] = None,
        blocked_domains: Optional[Set[str]] = None
    ):
        self.allow_private_ips = allow_private_ips
        self.allowed_schemes = allowed_schemes or {'http', 'https'}
        self.allowed_domains = allowed_domains
        self.blocked_domains = blocked_domains or set()

    def is_private_ip(self, ip_str: str) -> bool:
        """Check if IP is private."""
=======
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

        # Resolve hostname to IP
>>>>>>> main
        try:
            ip = ipaddress.ip_address(ip_str)
            for blocked_range in BLOCKED_IP_RANGES:
                if ip in blocked_range:
                    return True
            return False
<<<<<<< HEAD
        except ValueError:
            return False

    def is_metadata_endpoint(self, hostname: str) -> bool:
        """Check if hostname is a known cloud metadata endpoint."""
        metadata_hosts = {
            '169.254.169.254',
            'metadata.google.internal',
            'instance-data',
            '100.100.100.200'
        }
        return hostname.lower() in metadata_hosts

    def validate_url(self, url: str) -> Tuple[bool, str]:
        """Validate URL against SSRF policies."""
        try:
            parsed = urlparse(url)
            if not parsed.scheme or parsed.scheme not in self.allowed_schemes:
                return False, f"Scheme {parsed.scheme} not allowed"

            if not parsed.hostname:
                return False, "No hostname provided"

            hostname = parsed.hostname.lower()

            if self.allowed_domains and hostname not in self.allowed_domains:
                return False, f"Domain {hostname} not in allowlist"

            if hostname in self.blocked_domains:
                return False, f"Domain {hostname} is blocked"

            if self.is_metadata_endpoint(hostname):
                return False, "Metadata endpoint access blocked"

            if not self.allow_private_ips:
                # DNS Resolution for protection against rebinding
                try:
                    addr_info = socket.getaddrinfo(hostname, None)
                    for info in addr_info:
                        ip_str = info[4][0]
                        if self.is_private_ip(ip_str):
                            return False, f"Hostname resolves to private IP: {ip_str}"
                except socket.gaierror:
                    pass

            return True, ""
        except Exception as e:
            return False, str(e)


def create_ssrf_safe_session(
    allowed_domains: Optional[Set[str]] = None,
    timeout: float = 30.0
) -> httpx.Client:
    """Create a synchronous SSRF-safe session."""
    return httpx.Client(timeout=timeout)
=======

        # Check if IP is in blocked ranges
        for blocked_range in BLOCKED_IP_RANGES:
            if ip in blocked_range:
                logger.error(
                    f"Blocked request to private IP: {ip} "
                    f"(range: {blocked_range}) for URL: {url}"
                )
                return False

        # Check protocol
        if parsed.scheme not in ('http', 'https'):
            logger.error(f"Blocked request with unsupported scheme: {parsed.scheme}")
            return False

        return True

    except Exception as e:
        logger.error(f"Error checking URL safety: {e}")
        return False
>>>>>>> main


def create_ssrf_safe_async_session(
    timeout: float = 30.0,
    follow_redirects: bool = False,
    max_redirects: int = 0
) -> httpx.AsyncClient:
<<<<<<< HEAD
    """Create an async SSRF-safe session."""
=======
    """
    Create SSRF-safe async HTTP client.
    
    Args:
        timeout: Request timeout in seconds
        follow_redirects: Whether to follow redirects
        max_redirects: Maximum number of redirects
        
    Returns:
        Configured async HTTP client
    """
    # Custom transport that checks URLs before connecting
    class SSRFSafeTransport(httpx.AsyncHTTPTransport):
        async def handle_async_request(self, request):
            url = str(request.url)
            if not is_safe_url(url):
                raise ValueError(f"Blocked SSRF attempt to: {url}")
            return await super().handle_async_request(request)

>>>>>>> main
    return httpx.AsyncClient(
        timeout=timeout,
        follow_redirects=follow_redirects,
        max_redirects=max_redirects
    )
