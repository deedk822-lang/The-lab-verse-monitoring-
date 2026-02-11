"""
Agent connector - streams LLM replies using the Ollama
SDK in a thread-pool to avoid blocking the event-loop.
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Dict, Iterable

import ollama
from fastapi import HTTPException, status

from server.telemetry import msg_sent_counter
from server.utils import resolve_local_model

log = logging.getLogger(__name__)

# ------------------------------------------------------------------
# Resolve the model once at import time
# ------------------------------------------------------------------
DEFAULT_MODEL = "llama2:7b"
MODEL_NAME = resolve_local_model(DEFAULT_MODEL)
log.info("Using Ollama model: %s", MODEL_NAME)


# ------------------------------------------------------------------
# Helper that runs in a thread-pool and consumes the Ollama stream.
# ------------------------------------------------------------------
def _ollama_stream(prompt: str) -> Dict[str, Any]:
    """
    Synchronous helper that drives ``ollama.generate`` and collects
    the streamed tokens. The function is run in a thread-pool to
    avoid blocking the async event loop.
    """
    try:
        iterator = ollama.generate(
            model=MODEL_NAME,
            prompt=prompt,
            stream=True,
            format="json",
        )
    except Exception as exc:
        log.exception("Error from ollama.generate")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    content_parts: list[str] = []
    total_tokens = 0

    for chunk in iterator:
        if chunk is None:
            continue
        if not chunk.get("done"):
            content_parts.append(chunk.get("response", ""))
        else:
            # The last chunk - token usage is reported here
            total_tokens = chunk.get("eval_count", 0)

    full_text = "".join(content_parts)
    return {"content": full_text, "usage": {"total_tokens": total_tokens or len(content_parts)}}


# ------------------------------------------------------------------
# Public async wrapper used by the main FastAPI app.
# ------------------------------------------------------------------
async def stream_agent_response(
    query: str,
    session_id: str,
) -> Dict[str, Any]:
    """
    Public, async wrapper that streams an Ollama response back
    to the calling component. It offloads the blocking I/O
    to a thread-pool, measures latency, and records telemetry.

    Returns:
        dict: {
            "response": <text>,
            "latency_ms": <ms>,
            "tokens": <int>
        }
    """
    start = time.time()
    try:
        # Run the blocking wrapper in a thread-pool.
        result = await asyncio.get_running_loop().run_in_executor(
            None,
            _ollama_stream,
            query,
        )
    except HTTPException:
        raise
    except Exception as exc:
        log.exception("Unexpected error in stream_agent_response")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        )

    latency_ms = int((time.time() - start) * 1000)

    # Record the outbound event
    msg_sent_counter.add(1, {"event": "agent_response", "session_id": session_id})

    return {
        "response": result["content"],
        "latency_ms": latency_ms,
        "tokens": result["usage"]["total_tokens"],
    }
