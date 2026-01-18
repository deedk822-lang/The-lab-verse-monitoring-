from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    PROJECT_NAME: str = "Rainmaker Orchestrator"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "secret-key-for-dev")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # GLM / Zhipu
    ZHIPU_API_KEY: str = os.getenv("ZAI_API_KEY", "") # Set via ENV

    # Alibaba Cloud
    ALIBABA_CLOUD_ACCESS_KEY_ID: str = os.getenv("ALIBABA_CLOUD_ACCESS_KEY_ID", "") # Set via ENV
    ALIBABA_CLOUD_SECRET_KEY: str = os.getenv("ALIBABA_CLOUD_SECRET_KEY", "")    # Set via ENV
    ALIBABA_CLOUD_REGION_ID: str = os.getenv("ALIBABA_CLOUD_REGION_ID", "cn-hangzhou")

    class Config:
        env_file = ".env"

settings = Settings()
