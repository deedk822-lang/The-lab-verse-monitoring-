import requests
import socket
import ipaddress
from urllib.parse import urlparse

class SecureSession:
    """SSRF-safe HTTP session with DNS validation"""

    ALLOWED_SCHEMES = ("http", "https")

    BLOCKED_NETWORKS = [
        ipaddress.ip_network("127.0.0.0/8"),
        ipaddress.ip_network("10.0.0.0/8"),
        ipaddress.ip_network("172.16.0.0/12"),
        ipaddress.ip_network("192.168.0.0/16"),
        ipaddress.ip_network("169.254.0.0/16"),
        ipaddress.ip_network("::1/128"),
        ipaddress.ip_network("fe80::/10"),
    ]

    def _resolve_and_check(self, hostname: str) -> bool:
        """Resolve hostname and check all IPs"""
        try:
            # Get all IPs for the hostname
            addr_info = socket.getaddrinfo(hostname, None)

            for info in addr_info:
                ip_str = info[4][0]
                ip = ipaddress.ip_address(ip_str)

                # Check against blocked networks
                for network in self.BLOCKED_NETWORKS:
                    if ip in network:
                        return False

                # Block multicast and reserved ranges
                if ip.is_multicast or ip.is_reserved:
                    return False

            return True
        except socket.gaierror:
            return False

    def _is_safe_url(self, url: str) -> bool:
        """Enhanced URL safety check"""
        try:
            parsed = urlparse(url)

            # Check protocol
            if parsed.scheme not in self.ALLOWED_SCHEMES:
                return False

            hostname = parsed.hostname
            if not hostname:
                return False

            # Check if already an IP
            try:
                ip = ipaddress.ip_address(hostname)
                for network in self.BLOCKED_NETWORKS:
                    if ip in network:
                        return False
            except ValueError:
                # It's a hostname, resolve it
                if not self._resolve_and_check(hostname):
                    return False

            return True

        except Exception:
            return False

    def get(self, url, **kwargs):
        if not self._is_safe_url(url):
            raise ValueError(f"URL is not safe: {url}")
        return requests.get(url, **kwargs)

    def post(self, url, **kwargs):
        if not self._is_safe_url(url):
            raise ValueError(f"URL is not safe: {url}")
        return requests.post(url, **kwargs)

    def put(self, url, **kwargs):
        if not self._is_safe_url(url):
            raise ValueError(f"URL is not safe: {url}")
        return requests.put(url, **kwargs)

    def delete(self, url, **kwargs):
        if not self._is_safe_url(url):
            raise ValueError(f"URL is not safe: {url}")
        return requests.delete(url, **kwargs)
