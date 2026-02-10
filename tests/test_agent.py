import pytest
from fastapi import HTTPException
from server.agent import stream_agent_response

@pytest.mark.asyncio
async def test_stream_agent_response_success(monkeypatch):
    """Test successful response streaming."""
    def fake_generate(*args, **kwargs):
        return [
            {"response": "Hi", "done": False},
            {"response": " ", "done": False},
            {"response": "there", "done": False},
            {"response": "", "done": True, "eval_count": 5},
        ]

    monkeypatch.setattr("ollama.generate", fake_generate)

    resp = await stream_agent_response("Hi there", session_id="abc")
    assert resp["response"] == "Hi there"
    assert resp["tokens"] == 5
    assert "latency_ms" in resp


@pytest.mark.asyncio
async def test_stream_agent_response_ollama_error(monkeypatch):
    """Test error handling when Ollama fails."""
    def fake_error(*args, **kwargs):
        raise RuntimeError("connection failed")

    monkeypatch.setattr("ollama.generate", fake_error)

    with pytest.raises(HTTPException) as exc:
        await stream_agent_response("test", session_id="xyz")
    assert exc.value.status_code == 502
    assert "connection failed" in exc.value.detail
