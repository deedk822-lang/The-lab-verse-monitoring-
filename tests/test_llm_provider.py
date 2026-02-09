"""Tests for agent/tools/llm_provider.py."""

import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

sys.modules.setdefault("vaal_ai_empire", MagicMock())
sys.modules.setdefault("vaal_ai_empire.api", MagicMock())
sys.modules.setdefault("vaal_ai_empire.api.sanitizers", MagicMock())
sys.modules.setdefault("vaal_ai_empire.api.secure_requests", MagicMock())


def test_generate_with_retry_retries_then_succeeds():
    from agent.tools.llm_provider import LLMConfig, OpenAIProvider, TaskType, LLMResponse

    provider = OpenAIProvider(LLMConfig(api_key="test", max_retries=3, retry_delay=0.001))
    calls = {"n": 0}

    async def _mock_generate(*_args, **_kwargs):
        calls["n"] += 1
        if calls["n"] < 3:
            raise RuntimeError("transient")
        return LLMResponse(text="ok", model="gpt-4o-mini", provider="OpenAI")

    with patch.object(provider, "generate", side_effect=_mock_generate):
        import asyncio
        result = asyncio.run(provider.generate_with_retry("hello", TaskType.TEXT_GENERATION))

    assert result.text == "ok"
    assert calls["n"] == 3


def test_factory_unknown_provider_raises():
    from agent.tools.llm_provider import LLMProviderFactory, LLMConfig

    with pytest.raises(ValueError):
        LLMProviderFactory.create("unknown", LLMConfig())


def test_initialize_from_env_openai_requires_api_key(monkeypatch):
    from agent.tools.llm_provider import initialize_from_env

    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
        initialize_from_env()
