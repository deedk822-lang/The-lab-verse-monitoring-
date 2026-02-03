import pytest
from fastapi import HTTPException

from server.agent import stream_agent_response


@pytest.fixture(autouse=True)
def mock_ollama(monkeypatch):
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
        raise RuntimeError("boom")

    monkeypatch.setattr("ollama.generate", bad_generate)

    with pytest.raises(HTTPException) as excinfo:
        await stream_agent_response("test", session_id="xyz")

    assert excinfo.value.status_code == 502
    assert "boom" in str(excinfo.value.detail)
