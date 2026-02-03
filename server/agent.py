"""Real agent connector – talks to a local Ollama endpoint."""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, Iterable

import ollama
from fastapi import HTTPException, status

from server.telemetry import msg_sent_counter
from server.utils import resolve_local_model

log = logging.getLogger(__name__)

DEFAULT_MODEL = "llama2:7b"
MODEL_NAME = resolve_local_model(DEFAULT_MODEL)

log.info("Using Ollama model – %s", MODEL_NAME)


async def _generate_response(prompt: str) -> Dict[str, Any]:
    """
    Calls Ollama synchronously in a thread-pool and aggregates tokens.

    Returns a dict with the final content and the total token count.
    """
    loop = asyncio.get_running_loop()
    try:
        response = await loop.run_in_executor(
            None,
            lambda: ollama.generate(
                model=MODEL_NAME,
                prompt=prompt,
                stream=True,
                format="json",
            ),
        )
        if asyncio.iscoroutine(response):
            response = await response
    except Exception as exc:
        log.exception("Error from Ollama")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    tokens = _extract_tokens(response)
    full_text = "".join(tokens)
    return {"content": full_text, "usage": {"total_tokens": len(tokens)}}


def _extract_tokens(response: Any) -> list[str]:
    if isinstance(response, dict):
        return [str(response.get("response", ""))]
    if response is None:
        return []
    chunks: Iterable[Dict[str, Any]] = response
    return [str(chunk.get("response", "")) for chunk in chunks if chunk is not None]


async def stream_agent_response(query: str, session_id: str) -> Dict[str, Any]:
    """
    Public, async wrapper that streams an Ollama response back to the caller.

    Returns a dict that includes response text, latency in ms, and token count.
    """
    loop = asyncio.get_running_loop()
    start = loop.time()
    result = await _generate_response(query)
    latency_ms = int((loop.time() - start) * 1000)

    msg_sent_counter.add(1, {"event": "agent_response", "session_id": session_id})

    return {
        "response": result["content"],
        "latency_ms": latency_ms,
        "tokens": result["usage"]["total_tokens"],
    }
