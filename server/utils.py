"""Shared utilities for local Open-Source model resolution."""

import json
from pathlib import Path


def resolve_local_model(default: str = "llama2:7b") -> str:
    """
    Resolve the model name from a local `model.json`, falling back to the provided default.
    
    Searches for `model.json` adjacent to this module; if the file exists and contains a truthy `"model"` value, that value is returned as a string. Any errors reading or parsing the file are ignored and the `default` is returned.
    
    Parameters:
        default (str): Fallback model name used when no valid `"model"` entry is found. Defaults to "llama2:7b".
    
    Returns:
        str: The configured model name, or `default` if none is available.
    """
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