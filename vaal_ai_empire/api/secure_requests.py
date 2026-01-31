"""
SSRF-safe HTTP client for external API calls.
Prevents Server-Side Request Forgery attacks.
"""

import ipaddress
import logging
import socket
from urllib.parse import urlparse
from typing import Optional, Set, Any, Tuple

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
    """Helper class for SSRF protection."""
    
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
        self.blocked_domains = blocked_domains

    def is_private_ip(self, ip_str: str) -> bool:
        """Check if an IP is private/internal."""
        try:
            ip = ipaddress.ip_address(ip_str)
            if ip.is_loopback or ip.is_private or ip.is_link_local or ip.is_multicast:
                return True
            for blocked_range in BLOCKED_IP_RANGES:
                if ip in blocked_range:
                    return True
            return False
        except ValueError:
            return False

    def is_metadata_endpoint(self, hostname_or_ip: str) -> bool:
        """Check if hostname or IP is cloud metadata endpoint."""
        if hostname_or_ip == "169.254.169.254":
            return True
        if "metadata.google.internal" in hostname_or_ip.lower():
            return True
        return False

    def is_safe_url(self, url: str) -> bool:
        """Check if URL is safe to request."""
        valid, _ = self.validate_url(url)
        return valid

    def validate_url(self, url: str) -> Tuple[bool, Optional[str]]:
        """Validate URL and return (is_valid, error_message)."""
        try:
            parsed = urlparse(url)

            # Check scheme
            if parsed.scheme not in self.allowed_schemes:
                return False, f"Scheme {parsed.scheme} is not allowed"

            # Check domain
            if not parsed.hostname:
                return False, "Missing hostname"

            hostname = parsed.hostname.lower()
            if self.is_metadata_endpoint(hostname):
                return False, "Metadata endpoint blocked"

            if self.allowed_domains and hostname not in self.allowed_domains:
                return False, f"Domain {hostname} is not in allowlist"
            if self.blocked_domains and hostname in self.blocked_domains:
                return False, f"Domain {hostname} is blocked"

            # Resolve hostname to IP if not allowing private IPs
            if not self.allow_private_ips:
                try:
                    # Use getaddrinfo to match test mock
                    addr_info = socket.getaddrinfo(hostname, None)
                    for family, kind, proto, canonname, sockaddr in addr_info:
                        ip_str = sockaddr[0]
                        if self.is_private_ip(ip_str) or self.is_metadata_endpoint(ip_str):
                            return False, f"Blocked private IP: {ip_str}"
                except (socket.gaierror, ValueError, IndexError):
                    return False, f"Could not resolve hostname: {hostname}"

            return True, None
        except Exception as e:
            return False, str(e)


def is_safe_url(url: str) -> bool:
    """Legacy helper function."""
    return SSRFBlocker().is_safe_url(url)


def create_ssrf_safe_async_session(
    timeout: float = 30.0,
    follow_redirects: bool = False,
    max_redirects: int = 0,
    allowed_domains: Optional[Set[str]] = None
) -> httpx.AsyncClient:
    """Create SSRF-safe async HTTP client."""
    
    blocker = SSRFBlocker(allowed_domains=allowed_domains)

    class SSRFSafeTransport(httpx.AsyncHTTPTransport):
        async def handle_async_request(self, request):
            url = str(request.url)
            if not blocker.is_safe_url(url):
                raise ValueError(f"Blocked SSRF attempt to: {url}")
            return await super().handle_async_request(request)

    return httpx.AsyncClient(
        transport=SSRFSafeTransport(),
        timeout=timeout,
        follow_redirects=follow_redirects,
        max_redirects=max_redirects,
        headers={'User-Agent': 'VAAL-AI-Empire/1.0'}
    )


def create_ssrf_safe_session(
    timeout: float = 30.0,
    follow_redirects: bool = False,
    max_redirects: int = 0,
    allowed_domains: Optional[Set[str]] = None
) -> httpx.Client:
    """Create SSRF-safe sync HTTP client."""

    blocker = SSRFBlocker(allowed_domains=allowed_domains)

    class SSRFSafeSyncTransport(httpx.HTTPTransport):
        def handle_request(self, request: httpx.Request) -> httpx.Response:
            url = str(request.url)
            if not blocker.is_safe_url(url):
                raise ValueError(f"Blocked SSRF attempt to: {url}")
            return super().handle_request(request)

    return httpx.Client(
        transport=SSRFSafeSyncTransport(),
        timeout=timeout,
        follow_redirects=follow_redirects,
        max_redirects=max_redirects,
        headers={'User-Agent': 'VAAL-AI-Empire/1.0'}
    )
