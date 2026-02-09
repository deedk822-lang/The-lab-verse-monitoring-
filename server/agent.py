 codex/add-initial-configuration-and-server-files
"""
Agent connector - streams LLM replies using the Ollama
SDK in a thread-pool to avoid blocking the event-loop.
"""

import asyncio
import logging
import time
from typing import Any, Dict

import ollama  # pip : pip install ollama

"""Real agent connector – talks to a local Ollama endpoint."""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, Iterable

import ollama
 codex/add-mypy-configuration-and-server-components
from fastapi import HTTPException, status

from server.telemetry import msg_sent_counter
from server.utils import resolve_local_model

log = logging.getLogger(__name__)

 codex/add-initial-configuration-and-server-files
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

DEFAULT_MODEL = "llama2:7b"
MODEL_NAME = resolve_local_model(DEFAULT_MODEL)

log.info("Using Ollama model – %s", MODEL_NAME)


async def _generate_response(prompt: str) -> Dict[str, Any]:
    """
 codex/add-mypy-configuration-and-server-components
    Calls Ollama synchronously in a thread-pool and aggregates tokens.

    Returns a dict with the final content and the total token count.

    Generate a text response for the given prompt using the local Ollama model.
    
    Executes the Ollama call in a thread pool, collects streamed token fragments, and returns the concatenated response text together with a token count.
    
    Returns:
        dict: A dictionary with keys:
            - "content": The full concatenated response text (str).
            - "usage": A dict containing "total_tokens" (int) with the number of tokens collected.
    
    Raises:
        HTTPException: Raised with a 502 Bad Gateway status when the Ollama call fails; the exception detail contains the original error message.
 codex/implement-real-ollama-integration
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
 codex/add-mypy-configuration-and-server-components
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

 codex/add-initial-configuration-and-server-files
    latency_ms = int((time.time() - start) * 1000)

    # Record the outbound event via the tiny counter defined in telemetry.py.
    # In production this could be a Prometheus Counter or an OpenTelemetry
    # metric. The labels are optional in the stub implementation.
    msg_sent_counter.add(1, {"event": "agent_response", "session_id": session_id})

    # Return the structure expected by the caller.

    tokens = _extract_tokens(response)
    full_text = "".join(tokens)
    return {"content": full_text, "usage": {"total_tokens": len(tokens)}}


def _extract_tokens(response: Any) -> list[str]:
 codex/add-mypy-configuration-and-server-components

    """
    Normalize an Ollama response into a flat list of token strings.
    
    Accepts a single response that may be a dict (single chunk), None, or an iterable of chunk dicts, and returns the chunk "response" values as strings in order.
    
    Parameters:
        response (Any): An Ollama response which can be:
            - dict: a single chunk with a "response" key,
            - None: no content,
            - Iterable[dict]: a sequence of chunk dictionaries that may include None entries.
    
    Returns:
        list[str]: A list of token strings extracted from the "response" field of each chunk. For a dict input this yields a one-item list; for None it yields an empty list; for an iterable it preserves order and skips None chunks.
    """
 codex/implement-real-ollama-integration
    if isinstance(response, dict):
        return [str(response.get("response", ""))]
    if response is None:
        return []
    chunks: Iterable[Dict[str, Any]] = response
    return [str(chunk.get("response", "")) for chunk in chunks if chunk is not None]


async def stream_agent_response(query: str, session_id: str) -> Dict[str, Any]:
    """
 codex/add-mypy-configuration-and-server-components
    Public, async wrapper that streams an Ollama response back to the caller.

    Returns a dict that includes response text, latency in ms, and token count.

    Request a response from the local Ollama model and return the final text with timing and token usage.
    
    Parameters:
        query (str): Prompt text sent to the model.
        session_id (str): Identifier used for telemetry tagging of the request.
    
    Returns:
        Dict[str, Any]: A dictionary with:
            - "response" (str): The concatenated text generated by the model.
            - "latency_ms" (int): Elapsed time to generate the response in milliseconds.
            - "tokens" (int): Total number of tokens returned by the model.
 codex/implement-real-ollama-integration
    """
    loop = asyncio.get_running_loop()
    start = loop.time()
    result = await _generate_response(query)
    latency_ms = int((loop.time() - start) * 1000)

    msg_sent_counter.add(1, {"event": "agent_response", "session_id": session_id})

 codex/add-mypy-configuration-and-server-components
    return {
        "response": result["content"],
        "latency_ms": latency_ms,
        "tokens": result["usage"]["total_tokens"],
 codex/add-initial-configuration-and-server-files
    }

 codex/add-mypy-configuration-and-server-components
    }

    }
 codex/implement-real-ollama-integration
 codex/add-mypy-configuration-and-server-components
