from __future__ import annotations

import logging
from functools import lru_cache
from typing import Literal, Optional

import torch
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


class HuggingFaceConfig(BaseSettings):
    """Hugging Face Models Configuration."""

    # Models
    model_diagnostic: str = "mistralai/Mistral-7B-Instruct-v0.3"
    model_planner: str = "microsoft/phi-2"
    model_executor: str = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
    model_validator: str = "mistralai/Mistral-7B-Instruct-v0.3"

    # Runtime
    device: str = "cuda" if torch.cuda.is_available() else "cpu"
    load_in_8bit: bool = True
    load_in_4bit: bool = False
    max_tokens: int = 2048
    temperature: float = 0.7
    top_p: float = 0.9

    # Hub/cache
    hf_cache_dir: str = "./models"
    hf_token: Optional[str] = None

    # Serving (optional)
    use_vllm: bool = False
    vllm_port: int = 8888

    class Config:
        env_prefix = "HF_"


class BitbucketConfig(BaseSettings):
    """Bitbucket-specific configuration."""

    workspace: str = "lab-verse-monitoring"
    username: str
    app_password: str
    webhook_secret: Optional[str] = None

    class Config:
        env_prefix = "BITBUCKET_"


class AgentConfig(BaseSettings):
    """Agent behavior."""

    max_retries: int = 3
    approval_timeout_seconds: int = 3600
    pipeline_wait_timeout_seconds: int = 1800
    cache_dir: str = "./cache"
    enable_caching: bool = True

    class Config:
        env_prefix = ""


class SecurityConfig(BaseSettings):
    enable_human_approval: bool = True
    enable_audit_logging: bool = True
    enable_rate_limiting: bool = True

    class Config:
        env_prefix = "ENABLE_"


class InfrastructureConfig(BaseSettings):
    environment: str = "production"
    log_level: str = "INFO"
    kubernetes_namespace: str = "lab-verse-monitoring"
    enable_metrics: bool = True
    metrics_port: int = 8001

    class Config:
        env_prefix = ""


class AppConfig(BaseSettings):
    pipeline_platform: Literal["bitbucket"] = "bitbucket"

    hf: HuggingFaceConfig = HuggingFaceConfig()
    bitbucket: BitbucketConfig = BitbucketConfig()
    agent: AgentConfig = AgentConfig()
    security: SecurityConfig = SecurityConfig()
    infrastructure: InfrastructureConfig = InfrastructureConfig()

    class Config:
        env_file = ".env.production"
        case_sensitive = False


@lru_cache
def get_config() -> AppConfig:
    cfg = AppConfig()
    logger.info("✅ Configuration loaded for %s", cfg.infrastructure.environment)
    logger.info("🤖 Using device: %s", cfg.hf.device)
    logger.info("📦 Models cache: %s", cfg.hf.hf_cache_dir)
    return cfg


config = get_config()
