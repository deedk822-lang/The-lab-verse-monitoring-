"""
SSRF-safe HTTP client for external API calls.
Prevents Server-Side Request Forgery attacks.
"""

import ipaddress
import socket
import logging
from typing import Optional, Set, Tuple, List
import httpx
import requests
from urllib.parse import urlparse

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
    """Raised when an SSRF attempt is blocked."""
    pass

class SSRFBlocker:
    """Validator for SSRF protection."""
    
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
        try:
            ip = ipaddress.ip_address(ip_str)
            return any(ip in net for net in BLOCKED_IP_RANGES)
        except ValueError:
            return False

    def is_metadata_endpoint(self, hostname: str) -> bool:
        """Check if hostname is a cloud metadata endpoint."""
        metadata_hostnames = {
            "metadata.google.internal",
            "169.254.169.254",
            "instance-data",
            "metadata"
        }
        return hostname in metadata_hostnames
        
    def validate_url(self, url: str) -> Tuple[bool, str]:
        """Validate URL for SSRF."""
        try:
            parsed = urlparse(url)

            if parsed.scheme not in self.allowed_schemes:
                return False, f"Scheme {parsed.scheme} not allowed"

            if not parsed.hostname:
                return False, "No hostname found"

            if self.blocked_domains and parsed.hostname in self.blocked_domains:
                return False, f"Domain {parsed.hostname} is blocked"

            if self.allowed_domains and parsed.hostname not in self.allowed_domains:
                return False, f"Domain {parsed.hostname} is not in allowlist"

            if self.is_metadata_endpoint(parsed.hostname):
                return False, "Metadata endpoint blocked"

            if not self.allow_private_ips:
                try:
                    # DNS Rebinding protection: resolve all IPs
                    addr_info = socket.getaddrinfo(parsed.hostname, parsed.port or (80 if parsed.scheme == 'http' else 443))
                    for info in addr_info:
                        ip_str = info[4][0]
                        if self.is_private_ip(ip_str):
                            return False, f"Hostname resolves to private IP: {ip_str}"
                except socket.gaierror:
                    return False, "Could not resolve hostname"

            return True, ""

        except Exception as e:
            return False, str(e)

def is_safe_url(url: str) -> bool:
    """Legacy helper."""
    blocker = SSRFBlocker()
    valid, _ = blocker.validate_url(url)
    return valid

def create_ssrf_safe_session(
    allowed_domains: Optional[Set[str]] = None,
    timeout: float = 30.0
) -> httpx.Client:
    """Create synchronous safe session."""
    blocker = SSRFBlocker(allowed_domains=allowed_domains)

    class SSRFSafeTransport(httpx.HTTPTransport):
        def handle_request(self, request):
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
    """Create async safe session."""
    blocker = SSRFBlocker()
    
    class SSRFSafeAsyncTransport(httpx.AsyncHTTPTransport):
        async def handle_async_request(self, request):
            url = str(request.url)
            valid, error = blocker.validate_url(url)
            if not valid:
                raise SSRFProtectionError(f"Blocked SSRF attempt: {error}")
            return await super().handle_async_request(request)
    
    return httpx.AsyncClient(
        transport=SSRFSafeAsyncTransport(),
        timeout=timeout,
        follow_redirects=follow_redirects,
        max_redirects=max_redirects
    )
