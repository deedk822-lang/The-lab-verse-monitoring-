import pytest
from fastapi import HTTPException

from server.agent import stream_agent_response


 codex/add-initial-configuration-and-server-files
@pytest.mark.asyncio
async def test_stream_agent_response_success(monkeypatch):
    # The helper that will be run in the thread-pool
    def fake_ollama(prompt):
        # simulate 3 tokens + final chunk
        return [
            {"response": "Hi", "done": False},
            {"response": " ", "done": False},
            {"response": "there", "done": False},
            {"response": "", "done": True, "eval_count": 5},
        ]

    monkeypatch.setattr("server.agent._ollama_stream", fake_ollama)

    resp = await stream_agent_response("Hi there", session_id="abc")
    assert resp["response"] == "Hi there"
    assert resp["tokens"] == 5

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
 codex/add-mypy-configuration-and-server-components
    assert resp["latency_ms"] >= 0


@pytest.mark.asyncio
 codex/add-initial-configuration-and-server-files
async def test_stream_agent_response_ollama_error(monkeypatch):
    def fake_error(prompt):
        raise RuntimeError("connection failed")

    monkeypatch.setattr("server.agent._ollama_stream", fake_error)

    with pytest.raises(HTTPException) as exc:
        await stream_agent_response("test", session_id="xyz")
    assert exc.value.status_code == 502
    assert "connection failed" in exc.value.detail

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
 codex/add-mypy-configuration-and-server-components
