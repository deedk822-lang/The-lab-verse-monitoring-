from pydantic_settings import BaseSettings
import os
from typing import List, Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "Rainmaker Orchestrator"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "fallback-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # GLM / Zhipu AI
    ZHIPU_API_KEY: str = os.getenv("ZAI_API_KEY", "")

    # Alibaba Cloud
    ALIBABA_CLOUD_ACCESS_KEY_ID: str = os.getenv("ALIBABA_CLOUD_ACCESS_KEY_ID", "")
    ALIBABA_CLOUD_SECRET_KEY: str = os.getenv("ALIBABA_CLOUD_SECRET_KEY", "")
    ALIBABA_CLOUD_REGION_ID: str = os.getenv("ALIBABA_CLOUD_REGION_ID", "cn-hangzhou")

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./rainmaker.db")

    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["*"]  # Should be restricted in production

    # Rate Limiting
    REQUESTS_PER_MINUTE: int = int(os.getenv("REQUESTS_PER_MINUTE", "60"))

    # Multi-tenancy
    ENABLE_MULTI_TENANCY: bool = os.getenv("ENABLE_MULTI_TENANCY", "True").lower() == "true"

    class Config:
        env_file = ".env"

settings = Settings()
