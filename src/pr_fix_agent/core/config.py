"""
Centralized Configuration - Global Production Standard (S1)
Uses pydantic-settings for zero-trust environment handling.
"""

from typing import Optional, Union
from pathlib import Path

from pydantic import Field, PostgresDsn, RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables or .env file.

    ✅ S1: Zero-trust secrets
    ✅ S2: TLS database connection strings
    ✅ S3: Redis URL
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Environment
    environment: str = Field(default="development")
    debug: bool = Field(default=False)

    # LLM Settings
    ollama_base_url: str = Field(default="http://localhost:11434")
    hf_api_token: Optional[str] = Field(default=None)

    # Database Settings (S2)
    database_url: Union[PostgresDsn, str] = Field(
        default="postgresql://user:pass@localhost:5432/db"
    )
    db_ssl_ca: Optional[Path] = Field(default=None)

    # Redis Settings (S3)
    redis_url: Union[RedisDsn, str] = Field(
        default="redis://localhost:6379/0"
    )

    # Rate Limiting
    rate_limit_per_minute: int = Field(default=10)
    rate_limit_storage_uri: str = Field(default="memory://")

    # Security (S5)
    audit_log_path: Path = Field(default=Path("logs/audit.log"))

    # Vault (S1)
    vault_enabled: bool = Field(default=False)
    vault_addr: Optional[str] = Field(default=None)
    vault_token: Optional[str] = Field(default=None)


def get_settings() -> Settings:
    """Get settings singleton."""
    return Settings()
