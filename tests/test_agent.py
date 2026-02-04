from fastapi import HTTPException
import pytest

from server.agent import stream_agent_response


@pytest.mark.asyncio
async def test_stream_agent_response_success(monkeypatch):
    # The helper that will be run in the thread-pool
    def fake_ollama(prompt):
        # simulate 3 tokens + final chunk
        return {"content": "Hi there", "usage": {"total_tokens": 5}}

    monkeypatch.setattr("server.agent._ollama_stream_sync", fake_ollama)

    resp = await stream_agent_response("Hi there", session_id="abc")
    assert resp["response"] == "Hi there"
    assert resp["tokens"] == 5

@pytest.fixture(autouse=True)
def mock_ollama(monkeypatch):
    """
    Provides a pytest monkeypatch that replaces `ollama.generate` with a simple tokenized responder.
    """
    def fake_generate(*args, **kwargs):
        prompt = kwargs.get("prompt", "")
        chunks = [{"response": part, "done": False} for part in prompt.split()]
        chunks.append({"response": "", "done": True, "eval_count": len(prompt.split())})
        return chunks

    monkeypatch.setattr("ollama.generate", fake_generate)


@pytest.mark.asyncio
async def test_stream_agent_response_basic():
    query = "Hello world"
    resp = await stream_agent_response(query, session_id="abc123")
    assert "response" in resp
    assert resp["tokens"] == len(query.split())
    assert resp["latency_ms"] >= 0


@pytest.mark.asyncio
async def test_stream_agent_response_ollama_error(monkeypatch):
    def fake_error(prompt):
        raise HTTPException(status_code=502, detail="connection failed")

    monkeypatch.setattr("server.agent._ollama_stream_sync", fake_error)

    with pytest.raises(HTTPException) as exc:
        await stream_agent_response("test", session_id="xyz")
    assert exc.value.status_code == 502
    assert "connection failed" in exc.value.detail

async def test_stream_agent_response_error(monkeypatch):
    def bad_generate(*_args, **_kwargs):
        """
        Helper used in tests that always raises a RuntimeError with the message "boom".

        Raises:
            RuntimeError: Raised unconditionally with message "boom".
        """
        raise RuntimeError("boom")

    monkeypatch.setattr("ollama.generate", bad_generate)

    with pytest.raises(HTTPException) as excinfo:
        await stream_agent_response("test", session_id="xyz")

    assert excinfo.value.status_code == 502
    assert "boom" in str(excinfo.value.detail)
