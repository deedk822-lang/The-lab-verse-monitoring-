"""Minimal stub for the ollama package used in tests."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any, Dict


def generate(*_args: Any, **_kwargs: Any) -> Iterator[dict[str, Any]]:
    """Return a dummy token stream for tests."""
    yield {"response": "dummy"}
