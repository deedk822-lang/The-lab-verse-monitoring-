"""
Configuration management for PR Fix Agent.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, PostgresDsn, RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Base
    app_name: str = "pr-fix-agent"
    version: str = "0.1.0"
    environment: Literal["development", "production", "test"] = "development"
    debug: bool = False

    # Security
    audit_log_path: Path = Field(default=Path("/app/logs/audit.log"))
    jwt_private_key_path: Path = Field(default=Path("/secrets/jwt-private-key.pem"))
    jwt_public_key_path: Path = Field(default=Path("/secrets/jwt-public-key.pem"))

    # Database
    database_url: str = Field(default="postgresql+psycopg2://prfixagent:password@localhost:5432/pr_fix_agent")
    db_ssl_ca: Path | None = None
    db_pool_size: int = 20
    db_max_overflow: int = 10
    db_pool_timeout: int = 30
    db_echo: bool = False

    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0")
    redis_max_connections: int = 10

    # Rate Limiting
    rate_limit_per_minute: int = 10

    # LLM
    ollama_base_url: str = "http://localhost:11434"

    # Observability
    log_level: str = "INFO"
    log_format: Literal["json", "console"] = "console"

    otel_enabled: bool = False
    otel_service_name: str = "pr-fix-agent"
    otel_exporter_otlp_endpoint: str | None = None

    # Feature Flags
    unleash_enabled: bool = False
    unleash_url: str | None = None
    unleash_api_token: str | None = None


@lru_cache
def get_settings() -> Settings:
    """Get cached settings."""
    return Settings()
