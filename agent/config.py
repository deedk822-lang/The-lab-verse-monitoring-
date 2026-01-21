from __future__ import annotations

import logging
from functools import lru_cache
from typing import Literal, Optional

import torch
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


class HuggingFaceConfig(BaseSettings):
    """Hugging Face Models Configuration (Local Inference)."""

    model_diagnostic: str = "mistralai/Mistral-7B-Instruct-v0.3"
    model_planner: str = "microsoft/phi-2"
    model_executor: str = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
    model_validator: str = "mistralai/Mistral-7B-Instruct-v0.3"

    device: str = "cuda" if torch.cuda.is_available() else "cpu"
    load_in_8bit: bool = True
    load_in_4bit: bool = False
    max_tokens: int = 2048
    temperature: float = 0.7
    top_p: float = 0.9

    hf_cache_dir: str = "./models"
    hf_token: Optional[str] = None

    class Config:
        env_prefix = "HF_"


class ZAIConfig(BaseSettings):
    """Z.AI API Configuration."""

    api_key: str
    model_diagnostic: str = "claude-3-5-sonnet-20241022"
    model_planner: str = "claude-3-5-sonnet-20241022"
    model_executor: str = "claude-3-sonnet-20240229"
    model_validator: str = "claude-3-sonnet-20240229"
    max_tokens: int = 3000

    class Config:
        env_prefix = "Z_AI_"


class QwenConfig(BaseSettings):
    """Qwen/Alibaba Dashscope API Configuration."""

    api_key: str
    model_diagnostic: str = "qwen-max"
    model_planner: str = "qwen-max"
    model_executor: str = "qwen-turbo"
    model_validator: str = "qwen-max"
    max_tokens: int = 2048

    class Config:
        env_prefix = "QWEN_"


class BitbucketConfig(BaseSettings):
    """Bitbucket-specific configuration."""

    workspace: str = "lab-verse-monitaring"
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
    """Main application configuration with multi-provider LLM support."""

    pipeline_platform: Literal["bitbucket"] = "bitbucket"
    llm_provider: Literal["huggingface", "z_ai", "qwen"] = "z_ai"

    hf: HuggingFaceConfig = HuggingFaceConfig()
    z_ai: ZAIConfig = ZAIConfig()
    qwen: QwenConfig = QwenConfig()
    bitbucket: BitbucketConfig = BitbucketConfig()
    agent: AgentConfig = AgentConfig()
    security: SecurityConfig = SecurityConfig()
    infrastructure: InfrastructureConfig = InfrastructureConfig()

    class Config:
        env_file = ".env.production"
        case_sensitive = False

    def get_llm_config(self):
        """Get the active LLM configuration based on provider selection."""
        if self.llm_provider == "z_ai":
            return self.z_ai
        elif self.llm_provider == "qwen":
            return self.qwen
        elif self.llm_provider == "huggingface":
            return self.hf
        else:
            raise ValueError(f"Unknown LLM provider: {self.llm_provider}")


@lru_cache
def get_config() -> AppConfig:
    cfg = AppConfig()
    logger.info("✅ Configuration loaded for %s", cfg.infrastructure.environment)
    logger.info("🤖 Using LLM provider: %s", cfg.llm_provider.upper())

    if cfg.llm_provider == "huggingface":
        logger.info("📦 Using device: %s", cfg.hf.device)
        logger.info("📂 Models cache: %s", cfg.hf.hf_cache_dir)
    elif cfg.llm_provider == "z_ai":
        logger.info("🌐 Using Z.AI API")
    elif cfg.llm_provider == "qwen":
        logger.info("🌐 Using Qwen/Dashscope API")

    return cfg


config = get_config()
