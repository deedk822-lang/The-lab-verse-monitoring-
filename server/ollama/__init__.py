"""Minimal stub for the ollama package used in tests."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict

if TYPE_CHECKING:
    from collections.abc import Iterator


def generate(*_args: Any, **_kwargs: Any) -> Iterator[dict[str, Any]]:
    """Return a dummy token stream for tests."""
    yield {"response": "dummy"}
