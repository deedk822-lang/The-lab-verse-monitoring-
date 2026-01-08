import pytest
from unittest.mock import patch, MagicMock
import anthropic
import os
import sys

# Add the script's directory to the Python path to allow importing it
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'scripts')))

from anthropic_validator import validate_anthropic_api

@pytest.fixture(autouse=True)
def manage_env_var():
    """Fixture to safely manage the API key environment variable for all tests."""
    original_value = os.environ.get("ANTHROPIC_API_KEY")
    os.environ["ANTHROPIC_API_KEY"] = "sk-ant-valid-key"
    yield
    if original_value is None:
        os.environ.pop("ANTHROPIC_API_KEY", None)
    else:
        os.environ["ANTHROPIC_API_KEY"] = original_value

def test_anthropic_key_valid():
    """Test with valid API key and successful API call."""
    with patch('anthropic.Anthropic') as mock_client:
        mock_message = MagicMock()
        mock_message.model = "claude-sonnet-4-5-20250929"
        mock_client.return_value.messages.create.return_value = mock_message

        ok, msg = validate_anthropic_api()
        assert ok is True
        assert "claude-sonnet-4-5" in msg

def test_anthropic_key_invalid():
    """Test with an invalid API key that causes an AuthenticationError."""
    with patch('anthropic.Anthropic') as mock_client:
        mock_client.return_value.messages.create.side_effect = \
            anthropic.AuthenticationError("Invalid API key", response=MagicMock(), body=None)

        ok, msg = validate_anthropic_api()
        assert ok is False
        assert "Invalid API key" in msg

def test_anthropic_connection_error():
    """Test a network failure scenario."""
    with patch('anthropic.Anthropic') as mock_client:
        mock_client.return_value.messages.create.side_effect = \
            anthropic.APIConnectionError(message="Connection timeout", request=MagicMock())

        ok, msg = validate_anthropic_api()
        assert ok is False
        assert "Connection failed" in msg

def test_anthropic_permission_denied_error():
    """Test a permission denied scenario."""
    with patch('anthropic.Anthropic') as mock_client:
        mock_client.return_value.messages.create.side_effect = \
            anthropic.PermissionDeniedError("Permission denied", response=MagicMock(), body=None)

        ok, msg = validate_anthropic_api()
        assert ok is False
        assert "lacks required permissions" in msg

def test_anthropic_rate_limit_error():
    """Test a rate limit exceeded scenario."""
    with patch('anthropic.Anthropic') as mock_client:
        mock_client.return_value.messages.create.side_effect = \
            anthropic.RateLimitError("Rate limit exceeded", response=MagicMock(), body=None)

        ok, msg = validate_anthropic_api()
        assert ok is False
        assert "Rate limit exceeded" in msg

def test_generic_api_error():
    """Test a generic API error from Anthropic."""
    with patch('anthropic.Anthropic') as mock_client:
        mock_client.return_value.messages.create.side_effect = \
            anthropic.APIError("Internal server error", request=MagicMock(), body=None)

        ok, msg = validate_anthropic_api()
        assert ok is False
        assert "API error" in msg

def test_no_api_key():
    """Test the case where the environment variable is not set."""
    os.environ.pop("ANTHROPIC_API_KEY", None)
    ok, msg = validate_anthropic_api()
    assert ok is False
    assert "ANTHROPIC_API_KEY environment variable not set" in msg

def test_invalid_api_key_format():
    """Test the case where the API key has an invalid format."""
    os.environ["ANTHROPIC_API_KEY"] = "invalid-key-format"
    ok, msg = validate_anthropic_api()
    assert ok is False
    assert "API key format invalid" in msg
