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
    """
    cfg_path = Path(__file__).parent / "model.json"

    if not cfg_path.is_file():
        log.debug("model.json not found - falling back to default: %s", default)
        return default

    try:
        data: Any = json.loads(cfg_path.read_text())
        if isinstance(data, dict) and "model" in data:
            return str(data["model"])
    except Exception as exc:
        log.warning("Failed to parse model.json: %s - using default: %s", exc, default)

    return default
