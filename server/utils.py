 codex/add-initial-configuration-and-server-files
"""
Utility helpers shared across the server package.
"""

import json
import logging
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)


def resolve_local_model(default: str = "llama2:7b") -> str:
    """
    Resolve the model name from a sibling ``model.json`` file.

    The file, if present, must be a JSON object that contains a
    top-level ``"model"`` key. If the file does not exist,
    cannot be parsed, or does not contain the key, the default
    value is returned instead.

    This is intentionally forgiving so that a misspelled
    ``model.json`` does not crash the whole service.
    """
    cfg_path = Path(__file__).parent / "model.json"

    if not cfg_path.is_file():
        log.debug("model.json not found - falling back to default: %s", default)
        return default

    try:
        data: Any = json.loads(cfg_path.read_text())
    except Exception as exc:  # pragma: no cover
        log.warning("Failed to parse model.json: %s - using default: %s", exc, default)
        return default

    if isinstance(data, dict) and "model" in data:
        return data["model"]

    log.warning(
        "model.json does not contain a dict with a 'model' key - using default: %s",
        default,
    )
    return default

"""Shared utilities for local Open-Source model resolution."""

import json
from pathlib import Path


def resolve_local_model(default: str = "llama2:7b") -> str:
 codex/add-mypy-configuration-and-server-components
    """Read `model.json` next to this file; return the configured model name."""

    """
    Resolve the model name from a local `model.json`, falling back to the provided default.
    
    Searches for `model.json` adjacent to this module; if the file exists and contains a truthy `"model"` value, that value is returned as a string. Any errors reading or parsing the file are ignored and the `default` is returned.
    
    Parameters:
        default (str): Fallback model name used when no valid `"model"` entry is found. Defaults to "llama2:7b".
    
    Returns:
        str: The configured model name, or `default` if none is available.
    """
 codex/implement-real-ollama-integration
    cfg_path = Path(__file__).parent / "model.json"
    if cfg_path.is_file():
        try:
            with cfg_path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
                model = data.get("model")
                if model:
                    return str(model)
        except (json.JSONDecodeError, OSError, TypeError, ValueError):
            pass
 codex/add-mypy-configuration-and-server-components
    return default

    return default
 codex/implement-real-ollama-integration
 codex/add-mypy-configuration-and-server-components
