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
            # Validate *all* resolved addresses (IPv4 + IPv6). If any resolved
            # address is unroutable/private, block the request.
            addrinfos = socket.getaddrinfo(hostname, None)
        except socket.gaierror:
            raise ConnectionError(f"Could not resolve hostname: {hostname}")

        resolved_ips: set[str] = set()
        for family, _socktype, _proto, _canonname, sockaddr in addrinfos:
            if family == socket.AF_INET:
                ip_str = sockaddr[0]
            elif family == socket.AF_INET6:
                ip_str = sockaddr[0]
            else:
                continue

            resolved_ips.add(ip_str)

        if not resolved_ips:
            raise ConnectionError(f"Could not resolve hostname: {hostname}")

        for ip_str in resolved_ips:
            try:
                ipobj = ipaddress.ip_address(ip_str)
            except ValueError:
                raise ConnectionError(f"Could not parse resolved IP: {ip_str}")

            if self.is_blocked_address(ipobj, allow_localhost=self.allow_localhost):
                raise ConnectionError(f"SSRF attempt blocked for IP: {ipobj}")

        return super().send(request, **kwargs)

    @staticmethod
    def is_blocked_address(ipobj: ipaddress._BaseAddress, *, allow_localhost: bool) -> bool:
        """Return True if the resolved IP should be blocked for SSRF safety."""
        if ipobj.is_loopback:
            return not allow_localhost

        # ipaddress flags catch most unroutable ranges for IPv4/IPv6.
        if (
            ipobj.is_private
            or ipobj.is_link_local
            or ipobj.is_reserved
            or ipobj.is_multicast
            or ipobj.is_unspecified
        ):
            return True

        # Shared address space (CGNAT) is not always marked as private.
        if ipobj.version == 4 and ipobj in ipaddress.ip_network("100.64.0.0/10"):
            return True

        return False


def create_ssrf_safe_session(allow_localhost=False):
    session = requests.Session()
    adapter = SSRFBlocker(allow_localhost=allow_localhost)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session
