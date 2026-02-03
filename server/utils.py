"""Shared utilities for local Open-Source model resolution."""

import json
from pathlib import Path


def resolve_local_model(default: str = "llama2:7b") -> str:
    """Read `model.json` next to this file; return the configured model name."""
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
    return default
