import pytest
from fastapi import HTTPException
from unittest.mock import MagicMock

from server.agent import stream_agent_response

@pytest.mark.asyncio
async def test_stream_agent_response_success(monkeypatch):
    """Test successful agent response streaming."""

    # Mock the internal _ollama_stream to avoid actual ollama calls
    def fake_ollama_stream(prompt):
        return {
            "content": "Hi there",
            "usage": {"total_tokens": 5}
        }

    monkeypatch.setattr("server.agent._ollama_stream", fake_ollama_stream)

    resp = await stream_agent_response("Hi there", session_id="abc")
    assert resp["response"] == "Hi there"
    assert resp["tokens"] == 5
    assert "latency_ms" in resp
    assert resp["latency_ms"] >= 0

@pytest.mark.asyncio
async def test_stream_agent_response_ollama_error(monkeypatch):
    """Test agent response when ollama raises an error."""

    def fake_error(prompt):
        raise HTTPException(status_code=502, detail="connection failed")

    monkeypatch.setattr("server.agent._ollama_stream", fake_error)

    with pytest.raises(HTTPException) as exc:
        await stream_agent_response("test", session_id="xyz")
    assert exc.value.status_code == 502
    assert "connection failed" in exc.value.detail

@pytest.mark.asyncio
async def test_stream_agent_response_unexpected_error(monkeypatch):
    """Test agent response when an unexpected error occurs."""

    def fake_unexpected_error(prompt):
        raise RuntimeError("boom")

    monkeypatch.setattr("server.agent._ollama_stream", fake_unexpected_error)

    with pytest.raises(HTTPException) as exc:
        await stream_agent_response("test", session_id="xyz")

    assert exc.value.status_code == 500
    assert "boom" in exc.value.detail
