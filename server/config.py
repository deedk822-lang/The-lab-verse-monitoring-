"""Configuration helpers for the agent service."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import os


@dataclass(frozen=True)
class Settings:
    """Settings loaded from environment variables."""

    jwt_secret: str
    redis_url: str
    oidc_discovery: str


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Load settings from environment variables."""
    return Settings(
        jwt_secret=os.environ.get("JWT_SECRET", ""),
        redis_url=os.environ.get("REDIS_URL", ""),
        oidc_discovery=os.environ.get("OIDC_DISCOVERY", ""),
    )
