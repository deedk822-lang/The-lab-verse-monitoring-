# tests/test_ssrf_protection.py
import pytest
from agents.background.worker import _validate_and_resolve_target

def test_blocks_localhost():
    """Test all localhost variations blocked"""
    blocked = [
        "http://localhost/",
        "http://127.0.0.1/",
        "http://0.0.0.0/",
        "http://[::1]/",
        "http://[::ffff:127.0.0.1]/",
        "http://0177.0.0.1/",  # octal
        "http://0x7f.0.0.1/",  # hex
        "http://127.1/",       # shortened
        "http://2130706433/",  # decimal
    ]

    for url in blocked:
        valid, msg, ip = _validate_and_resolve_target(url)
        assert not valid, f"{url} should be blocked"

def test_blocks_private_networks():
    """Test private IP ranges blocked"""
    # This requires mocking DNS
    pass  # Implement with pytest-mock

def test_blocks_dns_rebinding():
    """Test DNS rebinding attack blocked"""
    # Mock DNS to return different IPs
    # First: 8.8.8.8, Second: 127.0.0.1
    # Verify request uses first resolved IP
    pass  # Implement

def test_blocks_redirects():
    """Test redirects are blocked"""
    # Mock server that returns 302
    # Verify request fails
    pass  # Implement

def test_allows_valid_external():
    """Test valid external requests work"""
    valid, msg, ip = _validate_and_resolve_target("https://api.github.com/")
    assert valid
    assert ip is not None
