"""Minimal stub for the ollama package used in tests."""

from __future__ import annotations

from typing import Any, Dict, Iterator


def generate(*_args: Any, **_kwargs: Any) -> Iterator[Dict[str, Any]]:
    """Return a dummy token stream for tests."""
    yield {"response": "dummy"}
