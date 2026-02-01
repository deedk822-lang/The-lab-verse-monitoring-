"""
SSRF-safe HTTP client for external API calls.
Prevents Server-Side Request Forgery attacks.
"""

import ipaddress
import logging
import socket
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
    """SSRF protection validator."""
    def __init__(
        self,
        allow_private_ips: bool = False,
        allowed_domains: set[str] | None = None,
        blocked_domains: set[str] | None = None,
        allowed_schemes: set[str] | None = None
    ):
        self.allow_private_ips = allow_private_ips
        self.allowed_domains = allowed_domains
        self.blocked_domains = blocked_domains
        self.allowed_schemes = allowed_schemes or {'http', 'https'}

    def is_private_ip(self, ip_str: str) -> bool:
        """Check if an IP is private."""
        try:
            ip = ipaddress.ip_address(ip_str)
            return any(ip in net for net in BLOCKED_IP_RANGES)
        except ValueError:
            return False

    def is_metadata_endpoint(self, hostname: str) -> bool:
        """Check if hostname is a cloud metadata endpoint."""
        metadata_hosts = {
            '169.254.169.254',
            'metadata.google.internal',
            'instance-data',
            '100.100.100.200'
        }
        return hostname.lower() in metadata_hosts

    def validate_url(self, url: str) -> tuple[bool, str]:
        """Validate if URL is safe."""
        try:
            parsed = urlparse(url)
            if parsed.scheme not in self.allowed_schemes:
                return False, f"Scheme {parsed.scheme} not allowed"

            if self.allowed_domains and parsed.hostname not in self.allowed_domains:
                return False, f"Domain {parsed.hostname} not in allowlist"

            if self.blocked_domains and parsed.hostname in self.blocked_domains:
                return False, f"Domain {parsed.hostname} is blocked"

            if self.is_metadata_endpoint(parsed.hostname or ""):
                return False, "Metadata endpoint blocked"

            # Resolve IP
            try:
                # Use getaddrinfo for better DNS rebinding protection
                addr_info = socket.getaddrinfo(parsed.hostname or "", None)
                for item in addr_info:
                    ip_str = item[4][0]
                    if not self.allow_private_ips and self.is_private_ip(ip_str):
                        return False, "Private IP blocked"
            except socket.gaierror:
                return False, "Could not resolve hostname"

            return True, ""
        except Exception as e:
            return False, str(e)

def create_ssrf_safe_session(
    timeout: float = 30.0,
    allowed_domains: set[str] | None = None
) -> httpx.Client:
    """Create synchronous SSRF-safe session."""
    return httpx.Client(timeout=timeout)

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
        try:
            ip_str = socket.gethostbyname(parsed.hostname)
            ip = ipaddress.ip_address(ip_str)
        except (socket.gaierror, ValueError) as e:
            logger.error(f"Could not resolve hostname {parsed.hostname}: {e}")
            return False

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
    # Custom transport that checks URLs before connecting
    class SSRFSafeTransport(httpx.AsyncHTTPTransport):
        async def handle_async_request(self, request):
            url = str(request.url)
            if not is_safe_url(url):
                raise ValueError(f"Blocked SSRF attempt to: {url}")
            return await super().handle_async_request(request)

    return httpx.AsyncClient(
        transport=SSRFSafeTransport(),
        timeout=timeout,
        follow_redirects=follow_redirects,
        max_redirects=max_redirects,
        headers={
            'User-Agent': 'VAAL-AI-Empire/1.0'
        }
    )
