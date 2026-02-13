from fastapi import HTTPException
import pytest

from server.agent import stream_agent_response


@pytest.mark.asyncio
async def test_stream_agent_response_success(monkeypatch):
    # The helper that will be run in the thread-pool
    def fake_ollama_stream(prompt):
        return {"content": "Hi there", "usage": {"total_tokens": 5}}

    monkeypatch.setattr("server.agent._ollama_stream", fake_ollama_stream)

    resp = await stream_agent_response("Hi there", session_id="abc")
    assert resp["response"] == "Hi there"
    assert resp["tokens"] == 5
    assert resp["latency_ms"] >= 0


@pytest.mark.asyncio
async def test_stream_agent_response_ollama_error(monkeypatch):
    def fake_error(prompt):
        raise RuntimeError("connection failed")

    monkeypatch.setattr("server.agent._ollama_stream", fake_error)

    with pytest.raises(HTTPException) as exc:
        await stream_agent_response("test", session_id="xyz")
    assert exc.value.status_code == 502
    assert "connection failed" in exc.value.detail
