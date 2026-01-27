import pytest
from unittest.mock import AsyncMock, patch, Mock
import httpx

# Make sure the app path is correct for imports
import sys
sys.path.insert(0, '.')

from vaal_ai_empire.api.cohere import CohereAPI

@pytest.fixture
def mock_httpx_client():
    """Fixture to mock the httpx.AsyncClient."""
    mock_response = AsyncMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "text": "This is a test response.",
        "meta": {
            "billed_units": {
                "input_tokens": 10,
                "output_tokens": 20
            }
        }
    }
    # Crucially, mock the raise_for_status method to prevent real exceptions
    mock_response.raise_for_status = Mock()

    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.post.return_value = mock_response
    mock_client.aclose = AsyncMock()
    return mock_client

# Corrected patch target to where the function is looked up (in the cohere module)
@patch('vaal_ai_empire.api.cohere.create_ssrf_safe_async_session')
@pytest.mark.asyncio
async def test_generate_content_async(mock_create_session, mock_httpx_client):
    """Test that the refactored generate_content method works as expected."""
    # Arrange
    mock_create_session.return_value = mock_httpx_client

    with patch.dict('os.environ', {'COHERE_API_KEY': 'test_key'}):
        api = CohereAPI()

    # Act
    prompt = "Test prompt"
    result = await api.generate_content(prompt)

    # Assert
    assert "text" in result
    assert result["text"] == "This is a test response."
    assert "usage" in result
    assert result["usage"]["input_tokens"] == 10

    # Verify the mock was used as expected
    mock_httpx_client.post.assert_called_once()
    mock_response = mock_httpx_client.post.return_value
    mock_response.raise_for_status.assert_called_once()

    await api.close()


@patch('vaal_ai_empire.api.cohere.create_ssrf_safe_async_session')
@pytest.mark.asyncio
async def test_generate_email_sequence_concurrently(mock_create_session, mock_httpx_client):
    """Test that the email sequence generation calls API concurrently."""
    # Arrange
    mock_create_session.return_value = mock_httpx_client

    with patch.dict('os.environ', {'COHERE_API_KEY': 'test_key'}):
        api = CohereAPI()

    # Act
    days = 3
    sequence = await api.generate_email_sequence("bakery", days=days)

    # Assert
    assert mock_httpx_client.post.call_count == days
    assert len(sequence) == days
    # The mock returns the same text for each call, so the subject will be the same
    assert sequence[0]['subject'] == "This is a test response."

    await api.close()
