import socket
import ipaddress
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
            addrinfos = socket.getaddrinfo(hostname, None)
            ip_addresses = {ai[4][0] for ai in addrinfos}
        except socket.gaierror:
            raise ConnectionError(f"Could not resolve hostname: {hostname}")

        if any(self.is_private(ip) for ip in ip_addresses):
            if self.allow_localhost and all(
                ipaddress.ip_address(ip).is_loopback for ip in ip_addresses
            ):
                pass
            else:
                raise ConnectionError(f"SSRF attempt blocked for IPs: {sorted(ip_addresses)}")

        return super().send(request, **kwargs)

    @staticmethod
    def is_private(ip):
        try:
            ip_obj = ipaddress.ip_address(ip)
            return (
                ip_obj.is_private
                or ip_obj.is_loopback
                or ip_obj.is_link_local
                or ip_obj.is_reserved
                or ip_obj.is_multicast
            )
        except ValueError:
            return False


def create_ssrf_safe_session(allow_localhost=False):
    session = requests.Session()
    adapter = SSRFBlocker(allow_localhost=allow_localhost)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session
