import pytest
import requests
from security.secure_session import SecureSession

def test_ssrf_protection(mocker):
    """Test SSRF blocking"""
    mocker.patch('requests.get')
    session = SecureSession()

    # Should block localhost
    with pytest.raises(ValueError):
        session.get("http://127.0.0.1/admin")

    # Should block private networks
    with pytest.raises(ValueError):
        session.get("http://192.168.1.1/config")

    # Should allow valid domains
    session.get("https://www.google.com")
    requests.get.assert_called_once_with("https://www.google.com")
