import ipaddress
import socket
from urllib.parse import urlparse

import requests
from requests.adapters import HTTPAdapter
from requests.exceptions import ConnectionError


class SSRFBlocker(HTTPAdapter):
    def __init__(self, *args, **kwargs):
        self.allow_localhost = kwargs.pop("allow_localhost", False)
        super().__init__(*args, **kwargs)

    def send(self, request, **kwargs):
        parsed_url = urlparse(request.url)
        hostname = parsed_url.hostname

        if not hostname:
            raise ConnectionError(f"Invalid URL: {request.url}")

        try:
            # Get all possible IP addresses for the hostname (IPv4 and IPv6)
            addr_info = socket.getaddrinfo(hostname, None)
            ip_addresses = [info[4][0] for info in addr_info]
        except socket.gaierror:
            raise ConnectionError(f"Could not resolve hostname: {hostname}")

        for ip in ip_addresses:
            if self.is_private(ip):
                if self.allow_localhost and self.is_loopback(ip):
                    continue
                else:
                    raise ConnectionError(f"SSRF attempt blocked for IP: {ip}")

        return super().send(request, **kwargs)

    @staticmethod
    def is_private(ip_str):
        try:
            ip = ipaddress.ip_address(ip_str)
            return (
                ip.is_private
                or ip.is_loopback
                or ip.is_link_local
                or ip.is_multicast
                or ip.is_reserved
                or ip.is_unspecified
            )
        except ValueError:
            return True  # If we can't parse it, safer to block

    @staticmethod
    def is_loopback(ip_str):
        try:
            ip = ipaddress.ip_address(ip_str)
            return ip.is_loopback
        except ValueError:
            return False


def create_ssrf_safe_session(allow_localhost=False):
    session = requests.Session()
    adapter = SSRFBlocker(allow_localhost=allow_localhost)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session
