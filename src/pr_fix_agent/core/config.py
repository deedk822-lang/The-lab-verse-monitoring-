"""
Core configuration management for PR Fix Agent
"""

from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class DatabaseSettings(BaseSettings):
    """Database configuration"""

    url: str = Field(default="postgresql://localhost:5432/pr_fix_agent", alias="DATABASE_URL")
    pool_size: int = Field(default=10, ge=1, le=100)
    max_overflow: int = Field(default=20, ge=0, le=100)
    pool_timeout: int = Field(default=30, ge=1)
    pool_recycle: int = Field(default=3600, ge=60)

    @field_validator("url")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        if not v.startswith(("postgresql://", "postgresql+asyncpg://")):
            raise ValueError("Database URL must be a PostgreSQL connection string")
        return v


class RedisSettings(BaseSettings):
    """Redis configuration"""

    url: str = Field(default="redis://localhost:6379", alias="REDIS_URL")
    db: int = Field(default=0, ge=0, le=15)
    password: Optional[str] = Field(default=None, alias="REDIS_PASSWORD")
    ssl: bool = Field(default=False)
    max_connections: int = Field(default=20, ge=1, le=100)


class SecuritySettings(BaseSettings):
    """Security configuration"""

    secret_key: str = Field(default="change-me-in-production", alias="SECRET_KEY", min_length=32)
    jwt_secret: str = Field(default="change-me-in-production", alias="JWT_SECRET", min_length=32)
    jwt_algorithm: str = Field(default="HS256")
    jwt_expiration_hours: int = Field(default=24, ge=1, le=168)

    # Rate limiting
    rate_limit_requests: int = Field(default=100, ge=1)
    rate_limit_window_seconds: int = Field(default=60, ge=1)

    # SSRF protection
    allowed_domains: list[str] = Field(default_factory=lambda: ["github.com", "api.github.com"])
    blocked_domains: list[str] = Field(default_factory=list)

    # Input validation
    max_input_length: int = Field(default=10000, ge=100, le=100000)
    max_file_size_mb: int = Field(default=10, ge=1, le=100)


class ObservabilitySettings(BaseSettings):
    """Observability configuration"""

    log_level: str = Field(default="INFO", regex="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    log_format: str = Field(default="json")
    enable_tracing: bool = Field(default=True)
    enable_metrics: bool = Field(default=True)

    # Prometheus
    metrics_port: int = Field(default=9090, ge=1024, le=65535)

    # OpenTelemetry
    otlp_endpoint: Optional[str] = Field(default=None, alias="OTLP_ENDPOINT")
    service_name: str = Field(default="pr-fix-agent")
    service_version: str = Field(default="0.1.0")


class LLMSettings(BaseSettings):
    """LLM provider configuration"""

    # OpenAI
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    openai_base_url: Optional[str] = Field(default=None, alias="OPENAI_BASE_URL")

    # Cohere
    cohere_api_key: Optional[str] = Field(default=None, alias="COHERE_API_KEY")

    # HuggingFace
    huggingface_api_key: Optional[str] = Field(default=None, alias="HUGGINGFACE_API_KEY")
    huggingface_model: str = Field(default="microsoft/DialoGPT-medium")

    # Ollama
    ollama_base_url: str = Field(default="http://localhost:11434")
    ollama_model: str = Field(default="codellama:7b-instruct")

    # Cost tracking
    enable_cost_tracking: bool = Field(default=True)
    cost_budget_daily: float = Field(default=10.0, ge=0.0)


class Settings(BaseSettings):
    """Main application settings"""

    # Environment
    environment: str = Field(default="development", regex="^(development|staging|production)$")
    debug: bool = Field(default=False)

    # API
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000, ge=1024, le=65535)
    api_workers: int = Field(default=1, ge=1, le=16)

    # Sub-settings
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    observability: ObservabilitySettings = Field(default_factory=ObservabilitySettings)
    llm: LLMSettings = Field(default_factory=LLMSettings)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        env_nested_delimiter = "__"


# Global settings instance
settings = Settings()