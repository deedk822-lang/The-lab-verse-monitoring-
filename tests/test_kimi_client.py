from unittest.mock import patch, AsyncMock, MagicMock
import pytest

@pytest.mark.asyncio
@patch('rainmaker_orchestrator.clients.kimi.AsyncOpenAI')  # Fix: patch at import site
async def test_generate_chat_completion_success(mock_openai_class):
    """Test successful chat completion generation."""

    # Setup mock
    mock_client = AsyncMock()
    mock_openai_class.return_value = mock_client

    mock_completion = MagicMock()
    mock_completion.choices = [
        MagicMock(
            message=MagicMock(
                content="Test hotfix response",
                role="assistant"
            ),
            finish_reason="stop"
        )
    ]

    mock_client.chat.completions.create = AsyncMock(return_value=mock_completion)

    # Test
    from rainmaker_orchestrator.clients.kimi import KimiApiClient

    client = KimiApiClient(api_key="test-key")
    result = await client.generate_chat_completion(
        messages=[{"role": "user", "content": "test"}]
    )

    assert result == "Test hotfix response"
    mock_client.chat.completions.create.assert_awaited_once()