import pytest
from unittest.mock import AsyncMock, patch
from openai import APITimeoutError, APIStatusError
from clients.kimi import KimiApiClient

@pytest.mark.asyncio
async def test_generate_hotfix_success():
    with patch('openai.AsyncOpenAI') as mock_openai:
        mock_completion = AsyncMock()
        mock_completion.choices = [type('Choice', (), {'message': type('Message', (), {'content': 'mocked hotfix'})})()]
        mock_openai.return_value.chat.completions.create.return_value = mock_completion

        client = KimiApiClient(api_key="fake_key")
        result = await client.generate_hotfix("test prompt")

        assert result == "mocked hotfix"
        mock_openai.return_value.chat.completions.create.assert_awaited_once()

@pytest.mark.asyncio
async def test_generate_hotfix_retry_on_timeout():
    with patch('openai.AsyncOpenAI') as mock_openai:
        mock_openai.return_value.chat.completions.create.side_effect = [
            APITimeoutError(request=None, message="Request timed out."),
            AsyncMock(choices=[type('Choice', (), {'message': type('Message', (), {'content': 'mocked hotfix'})})()])
        ]

        client = KimiApiClient(api_key="fake_key")
        result = await client.generate_hotfix("test prompt")

        assert result == "mocked hotfix"
        assert mock_openai.return_value.chat.completions.create.call_count == 2

@pytest.mark.asyncio
async def test_generate_hotfix_retry_on_rate_limit():
    with patch('openai.AsyncOpenAI') as mock_openai:
        mock_openai.return_value.chat.completions.create.side_effect = [
            APIStatusError(request=None, message="Rate limit exceeded.", response=AsyncMock(status_code=429)),
            AsyncMock(choices=[type('Choice', (), {'message': type('Message', (), {'content': 'mocked hotfix'})})()])
        ]

        client = KimiApiClient(api_key="fake_key")
        result = await client.generate_hotfix("test prompt")

        assert result == "mocked hotfix"
        assert mock_openai.return_value.chat.completions.create.call_count == 2

@pytest.mark.asyncio
async def test_generate_hotfix_fail_after_retries():
    with patch('openai.AsyncOpenAI') as mock_openai:
        mock_openai.return_value.chat.completions.create.side_effect = APITimeoutError(request=None, message="Request timed out.")

        client = KimiApiClient(api_key="fake_key")

        with pytest.raises(Exception, match="Failed to generate hotfix after multiple retries."):
            await client.generate_hotfix("test prompt", max_retries=2)

        assert mock_openai.return_value.chat.completions.create.call_count == 2
