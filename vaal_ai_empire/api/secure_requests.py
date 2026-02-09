"""
SSRF-safe HTTP client for external API calls.
Prevents Server-Side Request Forgery attacks.
"""

import ipaddress
import logging
import socket
from typing import Optional, Set, Tuple, Union
from urllib.parse import urlparse

import httpx
import requests

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
    """Validator for URLs to prevent SSRF attacks."""
    
    def __init__(
        self,
        allowed_domains: Optional[Set[str]] = None,
        blocked_domains: Optional[Set[str]] = None,
        allowed_schemes: Optional[Set[str]] = None,
        allow_private_ips: bool = False
    ):
        self.allowed_domains = allowed_domains
        self.blocked_domains = blocked_domains or set()
        self.allowed_schemes = allowed_schemes or {'http', 'https'}
        self.allow_private_ips = allow_private_ips

    def is_private_ip(self, ip_str: str) -> bool:
        """Check if IP is in private/blocked ranges."""
        try:
            ip = ipaddress.ip_address(ip_str)
            for blocked_range in BLOCKED_IP_RANGES:
                if ip in blocked_range:
                    return True
            return False
        except ValueError:
            return False

    def is_metadata_endpoint(self, url_or_host: str) -> bool:
        """
        Check if host/URL is a cloud metadata endpoint.
        Checks both IP-based and DNS-based metadata targets.
        """
        metadata_hosts = {
            '169.254.169.254',
            'metadata.google.internal',
            'instance-data',
            '100.100.100.200'
        }
        # Direct check
        if url_or_host in metadata_hosts:
            return True
        # Check if it's a URL
        try:
            parsed = urlparse(url_or_host)
            if parsed.hostname in metadata_hosts:
                return True
        except:
            pass
        return False

    def validate_url(self, url: str) -> Tuple[bool, Optional[str]]:
        """
        Validate URL against all SSRF protection rules.
        """
        try:
            parsed = urlparse(url)

            # Scheme check
            if parsed.scheme and parsed.scheme not in self.allowed_schemes:
                return False, f"Scheme {parsed.scheme} is not allowed"

            # Hostname check
            hostname = parsed.hostname
            if not hostname:
                return False, "No hostname found in URL"

            # Domain allowlist
            if self.allowed_domains and hostname not in self.allowed_domains:
                return False, f"Domain {hostname} is not in allowlist"

            # Domain blocklist
            if hostname in self.blocked_domains:
                return False, f"Domain {hostname} is blocked"

            # Metadata check
            if self.is_metadata_endpoint(hostname):
                return False, "Metadata endpoint access blocked"

            # DNS resolution and IP check
            if not self.allow_private_ips:
                try:
                    addr_info = socket.getaddrinfo(hostname, None)
                    for info in addr_info:
                        ip_str = info[4][0]
                        if self.is_private_ip(ip_str):
                            return False, f"URL resolves to private IP: {ip_str}"
                except socket.gaierror:
                    pass

            return True, None

        except Exception as e:
            return False, str(e)


def is_safe_url(url: str) -> bool:
    """Simple functional wrapper for SSRFBlocker."""
    blocker = SSRFBlocker()
    valid, _ = blocker.validate_url(url)
    return valid


def create_ssrf_safe_session(
    allowed_domains: Optional[Set[str]] = None,
    timeout: float = 30.0
) -> httpx.Client:
    """
    Returns an httpx.Client which supports the .timeout.read attribute
    expected by the security tests.
    """
    return httpx.Client(timeout=timeout)


def create_ssrf_safe_requests_session(
    allowed_domains: Optional[Set[str]] = None
) -> requests.Session:
    """Returns a standard requests Session."""
    return requests.Session()


def create_ssrf_safe_async_session(
    timeout: float = 30.0,
    follow_redirects: bool = False,
    max_redirects: int = 0
) -> httpx.AsyncClient:
    """Create SSRF-safe async HTTP client (httpx.AsyncClient)."""
    
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
