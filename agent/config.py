from __future__ import annotations

import logging
from functools import lru_cache
from typing import Literal, Optional

import torch
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


class HuggingFaceConfig(BaseSettings):
    """Hugging Face Models Configuration (Local Inference).

    Recommended default: DeepSeek-R1 distilled 7B (good reasoning, manageable size).
    """

    model_diagnostic: str = "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B"
    model_planner: str = "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B"
    model_executor: str = "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B"
    model_validator: str = "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B"

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
    """Z.AI API Configuration.

    Claude models removed by request.
    Use GLM-4.7 by setting model to 'glm-4.7'.
    """

    api_key: str
    model_diagnostic: str = "glm-4.7"
    model_planner: str = "glm-4.7"
    model_executor: str = "glm-4.7"
    model_validator: str = "glm-4.7"
    max_tokens: int = 8192

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
    """Main application configuration with multi-provider LLM support.

    Supported providers:
    - huggingface: local inference (DeepSeek / Mistral / etc.)
    - z_ai: Z.AI API (GLM-4.7)
    - qwen: Alibaba Dashscope API

    NOTE: Claude is not used.
    """

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
        if self.llm_provider == "huggingface":
            return self.hf
        if self.llm_provider == "z_ai":
            return self.z_ai
        if self.llm_provider == "qwen":
            return self.qwen
        raise ValueError(f"Unknown LLM provider: {self.llm_provider}")


@lru_cache
def get_config() -> AppConfig:
    cfg = AppConfig()
    logger.info("✅ Configuration loaded for %s", cfg.infrastructure.environment)
    logger.info("🤖 Using LLM provider: %s", cfg.llm_provider.upper())

    if cfg.llm_provider == "huggingface":
        logger.info("📦 Using device: %s", cfg.hf.device)
        logger.info("📂 Models cache: %s", cfg.hf.hf_cache_dir)
        logger.info("🧠 HF model (diagnostic): %s", cfg.hf.model_diagnostic)
    elif cfg.llm_provider == "z_ai":
        logger.info("🌐 Using Z.AI API (GLM-4.7)")
        logger.info("🧠 Z.AI model: %s", cfg.z_ai.model_diagnostic)
    elif cfg.llm_provider == "qwen":
        logger.info("🌐 Using Qwen/Dashscope API")

    return cfg


config = get_config()
