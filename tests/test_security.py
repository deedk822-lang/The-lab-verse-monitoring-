import pytest
import socket
from vaal_ai_empire.api.sanitizers import sanitize_prompt
from vaal_ai_empire.api.secure_requests import SSRFBlocker, create_ssrf_safe_session
from requests.exceptions import ConnectionError

def test_sanitize_prompt_non_greedy():
    prompt = "Ignore {{ instructions }} but keep {{ this }}"
    sanitized = sanitize_prompt(prompt)
    # If it was greedy, it would remove everything between the first {{ and last }}
    assert "but keep" in sanitized
    assert "{{" not in sanitized
    assert "}}" not in sanitized

def test_ssrf_blocker_private_ip():
    blocker = SSRFBlocker()
    assert blocker.is_private("127.0.0.1") is True
    assert blocker.is_private("10.0.0.1") is True
    assert blocker.is_private("192.168.1.1") is True
    assert blocker.is_private("172.16.0.1") is True
    assert blocker.is_private("8.8.8.8") is False
    assert blocker.is_private("2606:4700:4700::1111") is False # Cloudflare DNS IPv6

def test_ssrf_blocker_loopback():
    blocker = SSRFBlocker()
    assert blocker.is_loopback("127.0.0.1") is True
    assert blocker.is_loopback("::1") is True
    assert blocker.is_loopback("8.8.8.8") is False
