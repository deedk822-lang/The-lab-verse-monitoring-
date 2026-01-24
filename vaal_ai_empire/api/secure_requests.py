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
            ip_address = socket.gethostbyname(hostname)
        except socket.gaierror:
            raise ConnectionError(f"Could not resolve hostname: {hostname}")

        if self.is_private(ip_address):
            if self.allow_localhost and ip_address.startswith("127."):
                pass
            else:
                raise ConnectionError(f"SSRF attempt blocked for IP: {ip_address}")

        return super().send(request, **kwargs)

    @staticmethod
    def is_private(ip):
        try:
            # Check if the IP is in private ranges or is a loopback address
            return (
                ip.startswith("10.") or
                ip.startswith("172.") and 16 <= int(ip.split(".")[1]) <= 31 or
                ip.startswith("192.168.") or
                ip.startswith("127.")
            )
        except (ValueError, IndexError):
            return False


def create_ssrf_safe_session(allow_localhost=False):
    session = requests.Session()
    adapter = SSRFBlocker(allow_localhost=allow_localhost)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session
