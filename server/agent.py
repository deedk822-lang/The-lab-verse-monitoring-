"""
Agent connector - streams LLM replies using the Ollama
SDK in a thread-pool to avoid blocking the event-loop.
"""

import asyncio
import logging
import time
from typing import Any, Dict

import ollama  # pip : pip install ollama
from fastapi import HTTPException, status

from server.telemetry import msg_sent_counter
from server.utils import resolve_local_model

log = logging.getLogger(__name__)

# ------------------------------------------------------------------
# Resolve the model once at import time - it is read from
# ``utils.resolve_local_model`` so that a malformed model.json
# does not crash on import.
# ------------------------------------------------------------------
DEFAULT_MODEL = "llama2:7b"
MODEL_NAME = resolve_local_model(DEFAULT_MODEL)


# ------------------------------------------------------------------
# Helper that runs in a thread-pool and consumes the Ollama stream.
# ------------------------------------------------------------------
def _ollama_stream(prompt: str) -> Dict[str, Any]:
    """
    Synchronous helper that drives ``ollama.generate`` and collects
    the streamed tokens. The function is small enough to be run
    in a thread-pool without touching the async layer.
    """
    try:
        iterator = ollama.generate(
            model=MODEL_NAME,
            prompt=prompt,
            stream=True,
            format="json",
        )
    except Exception:
        log.exception("Error from ollama.generate")
        raise

    content_parts: list[str] = []
    total_tokens = 0

    for chunk in iterator:
        # The stream emits a chunk for every token; the last chunk
        # carries an extra ``done`` flag. Ollama's spec:
        #
        #   { "response": "...", "done": false }
        #   ...
        #   { "response": "...", "done": true, "eval_count": 42 }
        #
        # We keep the partial responses and, when ``done`` is true,
        # read the ``eval_count`` field. That is the actual token
        # count reported by the model.
        if not chunk.get("done"):
            content_parts.append(chunk.get("response", ""))
        else:
            # The last chunk - token usage is reported here
            total_tokens = chunk.get("eval_count", 0)

    full_text = "".join(content_parts)
    return {"content": full_text, "usage": {"total_tokens": total_tokens}}


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
    except Exception as exc:  # pragma: no cover
        # Anything from ollama.generate (network, parsing, etc.)
        # is wrapped into the HTTP status that the UI can consume.
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    latency_ms = int((time.time() - start) * 1000)

    # Record the outbound event via the tiny counter defined in telemetry.py.
    # In production this could be a Prometheus Counter or an OpenTelemetry
    # metric. The labels are optional in the stub implementation.
    msg_sent_counter.add(1, {"event": "agent_response", "session_id": session_id})

    # Return the structure expected by the caller.
    return {
        "response": result["content"],
        "latency_ms": latency_ms,
        "tokens": result["usage"]["total_tokens"],
    }
