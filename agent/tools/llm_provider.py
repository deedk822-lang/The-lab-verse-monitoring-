from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Optional

import httpx

from agent.config import config
from agent.tools.hf_model_loader import model_loader

logger = logging.getLogger(__name__)


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    async def inference(
        self, task: str, prompt: str, model_id: Optional[str] = None, max_tokens: int = 1024
    ) -> str:
        raise NotImplementedError

    @abstractmethod
    async def get_system_info(self) -> dict:
        raise NotImplementedError


class HuggingFaceProvider(LLMProvider):
    """Hugging Face local model provider (no external API calls)."""

    async def inference(
        self, task: str, prompt: str, model_id: Optional[str] = None, max_tokens: int = 1024
    ) -> str:
        if not model_id:
            llm_cfg = config.hf
            if task == "diagnostic":
                model_id = llm_cfg.model_diagnostic
            elif task == "planner":
                model_id = llm_cfg.model_planner
            elif task == "executor":
                model_id = llm_cfg.model_executor
            elif task == "validator":
                model_id = llm_cfg.model_validator
            else:
                raise ValueError(f"Unknown task: {task}")

        logger.info("🤖 Running Hugging Face inference (%s) using %s", task, model_id)

        await model_loader.load_model(model_id, task=task)
        result = await model_loader.inference(task, prompt, max_tokens=max_tokens)
        model_loader.unload_model(task)

        return result

    async def get_system_info(self) -> dict:
        return await model_loader.get_system_info()


class ZAIProvider(LLMProvider):
    """Z.AI API provider (GLM-4.7)."""

    def __init__(self):
        self.base_url = "https://api.z.ai/v1"
        self.api_key = config.z_ai.api_key
        self.client = httpx.AsyncClient(
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        )

    async def inference(
        self, task: str, prompt: str, model_id: Optional[str] = None, max_tokens: int = 1024
    ) -> str:
        if not model_id:
            llm_cfg = config.z_ai
            if task == "diagnostic":
                model_id = llm_cfg.model_diagnostic
            elif task == "planner":
                model_id = llm_cfg.model_planner
            elif task == "executor":
                model_id = llm_cfg.model_executor
            elif task == "validator":
                model_id = llm_cfg.model_validator
            else:
                raise ValueError(f"Unknown task: {task}")

        logger.info("🌐 Calling Z.AI API (%s) using %s", task, model_id)

        payload = {
            "model": model_id,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": 0.7,
        }

        response = await self.client.post(f"{self.base_url}/chat/completions", json=payload)
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"]

    async def get_system_info(self) -> dict:
        return {"provider": "z_ai", "api_key_set": bool(self.api_key), "base_url": self.base_url}

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()


class QwenProvider(LLMProvider):
    """Qwen/Alibaba Dashscope API provider."""

    def __init__(self):
        self.base_url = "https://dashscope.aliyuncs.com/api/v1"
        self.api_key = config.qwen.api_key
        self.client = httpx.AsyncClient(
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        )

    async def inference(
        self, task: str, prompt: str, model_id: Optional[str] = None, max_tokens: int = 1024
    ) -> str:
        if not model_id:
            llm_cfg = config.qwen
            if task == "diagnostic":
                model_id = llm_cfg.model_diagnostic
            elif task == "planner":
                model_id = llm_cfg.model_planner
            elif task == "executor":
                model_id = llm_cfg.model_executor
            elif task == "validator":
                model_id = llm_cfg.model_validator
            else:
                raise ValueError(f"Unknown task: {task}")

        logger.info("🌐 Calling Qwen/Dashscope API (%s) using %s", task, model_id)

        payload = {
            "model": model_id,
            "input": {"messages": [{"role": "user", "content": prompt}]},
            "parameters": {"max_tokens": max_tokens, "temperature": 0.7},
        }

        response = await self.client.post(
            f"{self.base_url}/services/aigc/text-generation/generation", json=payload
        )
        response.raise_for_status()
        result = response.json()
        return result["output"]["text"]

    async def get_system_info(self) -> dict:
        return {"provider": "qwen", "api_key_set": bool(self.api_key), "base_url": self.base_url}

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()


def get_llm_provider() -> LLMProvider:
    provider_name = config.llm_provider

    if provider_name == "huggingface":
        logger.info("✅ Using Hugging Face local models")
        return HuggingFaceProvider()
    if provider_name == "z_ai":
        logger.info("✅ Using Z.AI API (GLM-4.7)")
        return ZAIProvider()
    if provider_name == "qwen":
        logger.info("✅ Using Qwen/Dashscope API")
        return QwenProvider()

    raise ValueError(f"Unknown LLM provider: {provider_name}")


llm_provider = get_llm_provider()
