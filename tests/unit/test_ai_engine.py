import pytest
import asyncio
from unittest.mock import patch, MagicMock, mock_open, ANY
import os
import sys
from pathlib import Path

# Add project root to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.kimi_instruct.service import AIEngine, Task, TaskStatus, Priority

# Mock AI provider configuration
MOCK_AI_PROVIDERS_YAML = """
openrouter:
  primary: openrouter/anthropic/claude-sonnet-4
  fallbacks:
    - openrouter/google/gemini-2.5-flash
    - openrouter/meta-llama/llama-4-scout:free

direct_providers:
  - dashscope
  - openai

edge_local:
  - ollama:qwen2:7b
"""

@pytest.fixture
def mock_task():
    """Provides a default Task object for tests."""
    return Task(
        id="test_task_123",
        title="Test Task",
        description="A task for testing purposes.",
        status=TaskStatus.PENDING,
        priority=Priority.MEDIUM
    )

@pytest.fixture
def mock_env():
    """Mocks environment variables for API keys."""
    with patch.dict(os.environ, {
        "OPENROUTER_API_KEY": "fake-openrouter-key",
        "DASHSCOPE_API_KEY": "fake-dashscope-key",
        "OPENAI_API_KEY": "fake-openai-key"
    }):
        yield

@pytest.fixture
async def ai_engine(mock_env):
    """Provides an AIEngine instance with proper session cleanup."""
    with patch("builtins.open", mock_open(read_data=MOCK_AI_PROVIDERS_YAML)):
        engine = AIEngine(config={})
        yield engine
        await engine.close_session()


@pytest.mark.asyncio
async def test_routing_openrouter_primary_succeeds(ai_engine, mock_task):
    """
    Tests that the AIEngine successfully uses the OpenRouter primary model when it works.
    """
    # Mock the OpenRouter call to succeed
    future = asyncio.Future()
    future.set_result('{"analysis": "success_primary"}')
    ai_engine._call_openrouter = MagicMock(return_value=future)

    result = await ai_engine.analyze_task(mock_task)

    # Verify the correct model was called
    ai_engine._call_openrouter.assert_called_once_with(
        "openrouter/anthropic/claude-sonnet-4",
        ANY  # The prompt is complex, so we don't check it exactly
    )
    assert result == {"analysis": "success_primary"}

@pytest.mark.asyncio
async def test_routing_falls_back_to_second_openrouter_model(ai_engine, mock_task):
    """
    Tests that the AIEngine falls back to the second OpenRouter model if the primary fails.
    """
    # Create a future that will be returned by the successful call
    successful_future = asyncio.Future()
    successful_future.set_result('{"analysis": "success_fallback_1"}')

    # Mock the OpenRouter call to fail on the first model, succeed on the second
    ai_engine._call_openrouter = MagicMock(
        side_effect=[
            Exception("Primary model failed"),
            successful_future
        ]
    )

    result = await ai_engine.analyze_task(mock_task)

    # Verify it was called twice with the correct models in order
    assert ai_engine._call_openrouter.call_count == 2
    ai_engine._call_openrouter.assert_any_call("openrouter/anthropic/claude-sonnet-4", ANY)
    ai_engine._call_openrouter.assert_called_with("openrouter/google/gemini-2.5-flash", ANY)
    assert result == {"analysis": "success_fallback_1"}

@pytest.mark.asyncio
async def test_routing_falls_back_to_direct_provider(ai_engine, mock_task):
    """
    Tests that the AIEngine falls back to a direct provider if all OpenRouter models fail.
    """
    # Mock all OpenRouter calls to fail
    ai_engine._call_openrouter = MagicMock(side_effect=Exception("OpenRouter model failed"))

    # Mock the first direct provider (DashScope) to succeed
    future = asyncio.Future()
    future.set_result('{"analysis": "success_direct_dashscope"}')
    ai_engine._call_dashscope = MagicMock(return_value=future)

    result = await ai_engine.analyze_task(mock_task)

    # Verify OpenRouter was called for all its models
    assert ai_engine._call_openrouter.call_count == 3

    # Verify the direct provider was called
    ai_engine._call_dashscope.assert_called_once()
    assert result == {"analysis": "success_direct_dashscope"}

@pytest.mark.asyncio
async def test_routing_falls_back_to_second_direct_provider(ai_engine, mock_task):
    """
    Tests fallback to the second direct provider if OpenRouter and the first direct provider fail.
    """
    # Mock all OpenRouter calls to fail
    ai_engine._call_openrouter = MagicMock(side_effect=Exception("OpenRouter model failed"))

    # Mock the first direct provider to fail and the second to succeed
    ai_engine._call_dashscope = MagicMock(side_effect=Exception("DashScope failed"))
    future = asyncio.Future()
    future.set_result('{"analysis": "success_direct_openai"}')
    ai_engine._call_openai = MagicMock(return_value=future)

    result = await ai_engine.analyze_task(mock_task)

    # Verify OpenRouter and first direct provider were called
    assert ai_engine._call_openrouter.call_count == 3
    ai_engine._call_dashscope.assert_called_once()

    # Verify the second direct provider was called successfully
    ai_engine._call_openai.assert_called_once()
    assert result == {"analysis": "success_direct_openai"}

@pytest.mark.asyncio
async def test_routing_falls_back_to_heuristic_analysis(ai_engine, mock_task):
    """
    Tests that the engine falls back to heuristic analysis if all providers fail.
    """
    # Mock all provider calls to fail
    ai_engine._call_openrouter = MagicMock(side_effect=Exception("OpenRouter failed"))
    ai_engine._call_dashscope = MagicMock(side_effect=Exception("DashScope failed"))
    ai_engine._call_openai = MagicMock(side_effect=Exception("OpenAI failed"))

    # Mock the heuristic analysis to check if it's called
    ai_engine._heuristic_analysis = MagicMock(return_value={"analysis": "success_heuristic"})

    result = await ai_engine.analyze_task(mock_task)

    # Verify all providers were attempted
    assert ai_engine._call_openrouter.call_count == 3
    ai_engine._call_dashscope.assert_called_once()
    ai_engine._call_openai.assert_called_once()

    # Verify heuristic analysis was the final result
    ai_engine._heuristic_analysis.assert_called_once_with(mock_task)
    assert result == {"analysis": "success_heuristic"}