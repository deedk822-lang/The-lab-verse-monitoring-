"""
Utility helpers shared across the server package.
"""

import json
import logging
from pathlib import Path

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
        data = json.loads(cfg_path.read_text())
        if isinstance(data, dict) and "model" in data:
            return str(data["model"])
    except Exception as exc:  # pragma: no cover
        log.warning("Failed to parse model.json: %s - using default: %s", exc, default)
        return default

    log.warning(
        "model.json does not contain a dict with a 'model' key - using default: %s",
        default,
    )
    return default
