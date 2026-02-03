import pytest
from fastapi import HTTPException

from server.agent import stream_agent_response


@pytest.fixture(autouse=True)
def mock_ollama(monkeypatch):
 codex/add-mypy-configuration-and-server-components

    """
    Provides a pytest monkeypatch that replaces `ollama.generate` with a simple tokenized responder.
    
    Patches `ollama.generate` so that when called with a `prompt` keyword argument it returns a list of dictionaries of the form `{"response": word}` for each word in the prompt. Intended for use as an autouse test fixture to simulate streamable model output.
    """
 codex/implement-real-ollama-integration
    def fake_generate(*args, **kwargs):
        prompt = kwargs.get("prompt", "")
        return [{"response": part} for part in prompt.split()]

    monkeypatch.setattr("ollama.generate", fake_generate)


@pytest.mark.asyncio
async def test_stream_agent_response_success():
    query = "Hello world"
    resp = await stream_agent_response(query, session_id="abc123")
    assert "response" in resp
    assert resp["tokens"] == len(query.split())
    assert resp["latency_ms"] >= 0


@pytest.mark.asyncio
async def test_stream_agent_response_error(monkeypatch):
    def bad_generate(*_args, **_kwargs):
 codex/add-mypy-configuration-and-server-components

        """
        Helper used in tests that always raises a RuntimeError with the message "boom".
        
        Raises:
            RuntimeError: Raised unconditionally with message "boom".
        """
 codex/implement-real-ollama-integration
        raise RuntimeError("boom")

    monkeypatch.setattr("ollama.generate", bad_generate)

    with pytest.raises(HTTPException) as excinfo:
        await stream_agent_response("test", session_id="xyz")

    assert excinfo.value.status_code == 502
 codex/add-mypy-configuration-and-server-components
    assert "boom" in str(excinfo.value.detail)

    assert "boom" in str(excinfo.value.detail)
 codex/implement-real-ollama-integration
