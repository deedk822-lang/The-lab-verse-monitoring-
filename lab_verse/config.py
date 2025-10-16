def load_config(path=None):
    return {}

def mutate_config(cfg, outcomes):
    return cfg

import yaml, os
from pathlib import Path

ALIGNMENT = yaml.safe_load(Path(".alignment.yml").read_text())

def get_aligned_model(role: str) -> str:
    return ALIGNMENT["openrouter"]["models"][role]

def grafana_headers() -> dict:
    return {"Authorization": f"Bearer {os.getenv('GRAFANA_API_KEY')}"}