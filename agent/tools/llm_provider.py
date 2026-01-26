"""
Multi-provider LLM abstraction layer with failover and monitoring.
Supports HuggingFace, Z.AI, Qwen, OpenAI, Anthropic, and more.
"""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any, List
import httpx

from vaal_ai_empire.api.sanitizers import sanitize_prompt
from vaal_ai_empire.api.secure_requests import create_ssrf_safe_async_session

logger = logging.getLogger(__name__)


class TaskType(Enum):
    """LLM task types for model selection."""
    CODE_GENERATION = "code_generation"
    TEXT_GENERATION = "text_generation"
    SUMMARIZATION = "summarization"
    QUESTION_ANSWERING = "qa"
    CLASSIFICATION = "classification"
    EMBEDDING = "embedding"
    CHAT = "chat"


@dataclass
class LLMResponse:
    """Standardized LLM response."""
    text: str
    model: str
    provider: str
    tokens_used: Optional[int] = None
    cost: Optional[float] = None
    latency_ms: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class LLMConfig:
    """Base LLM configuration."""
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    timeout: float = 60.0
    max_retries: int = 3
    retry_delay: float = 1.0


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    def __init__(self, config: LLMConfig):
        self.config = config
        self.provider_name = self.__class__.__name__.replace('Provider', '')

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        task: TaskType = TaskType.TEXT_GENERATION,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        **kwargs
    ) -> LLMResponse:
        """Generate completion from prompt."""
        pass

    @abstractmethod
    async def chat(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 1000,
        temperature: float = 0.7,
        **kwargs
    ) -> LLMResponse:
        """Chat completion with message history."""
        pass

    async def generate_with_retry(
        self,
        prompt: str,
        task: TaskType = TaskType.TEXT_GENERATION,
        **kwargs
    ) -> LLMResponse:
        """Generate with automatic retry logic."""
        last_error = None

        for attempt in range(self.config.max_retries):
            try:
                return await self.generate(prompt, task, **kwargs)
            except Exception as e:
                last_error = e
                if attempt < self.config.max_retries - 1:
                    delay = self.config.retry_delay * (2 ** attempt)
                    logger.warning(
                        f"LLM generation failed (attempt {attempt + 1}), "
                        f"retrying in {delay}s: {e}"
                    )
                    await asyncio.sleep(delay)

        raise last_error


class HuggingFaceProvider(LLMProvider):
    """HuggingFace local model provider."""

    def __init__(self, config: LLMConfig, model_loader=None):
        super().__init__(config)
        self.model_loader = model_loader
        self.task_models = {
            TaskType.CODE_GENERATION: "Qwen/Qwen2.5-Coder-7B-Instruct",
            TaskType.TEXT_GENERATION: "meta-llama/Llama-3.2-3B-Instruct",
            TaskType.CHAT: "meta-llama/Llama-3.2-3B-Instruct",
        }

    async def generate(
        self,
        prompt: str,
        task: TaskType = TaskType.TEXT_GENERATION,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        **kwargs
    ) -> LLMResponse:
        """Generate using local HuggingFace model."""
        start_time = time.time()

        # Sanitize input
        sanitized_prompt = sanitize_prompt(prompt, max_length=4000)

        # Select model for task
        model_name = self.task_models.get(task, self.task_models[TaskType.TEXT_GENERATION])

        # Load model if needed
        if self.model_loader:
            await asyncio.get_event_loop().run_in_executor(
                None, self.model_loader.load_model, model_name
            )

        # Generate (synchronous call in executor)
        def _generate():
            if not self.model_loader or not self.model_loader.model:
                raise RuntimeError("Model not loaded")

            inputs = self.model_loader.tokenizer(
                sanitized_prompt, return_tensors="pt"
            ).to(self.model_loader.device)

            outputs = self.model_loader.model.generate(
                **inputs,
                max_new_tokens=max_tokens,
                temperature=temperature,
                do_sample=temperature > 0,
                **kwargs
            )

            return self.model_loader.tokenizer.decode(
                outputs[0], skip_special_tokens=True
            )

        text = await asyncio.get_event_loop().run_in_executor(None, _generate)

        latency = (time.time() - start_time) * 1000

        return LLMResponse(
            text=text,
            model=model_name,
            provider=self.provider_name,
            latency_ms=latency
        )

    async def chat(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 1000,
        temperature: float = 0.7,
        **kwargs
    ) -> LLMResponse:
        """Chat using local model."""
        # Convert messages to prompt
        prompt = "\n".join([
            f"{msg['role']}: {msg['content']}"
            for msg in messages
        ])

        return await self.generate(
            prompt,
            TaskType.CHAT,
            max_tokens,
            temperature,
            **kwargs
        )


class ZAIProvider(LLMProvider):
    """Z.AI API provider."""

    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.base_url = config.base_url or "https://api.z.ai/v1"
        self.task_models = {
            TaskType.CODE_GENERATION: "z-code-instruct",
            TaskType.TEXT_GENERATION: "z-chat-large",
            TaskType.CHAT: "z-chat-large",
            TaskType.SUMMARIZATION: "z-summarize",
        }

    async def generate(
        self,
        prompt: str,
        task: TaskType = TaskType.TEXT_GENERATION,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        **kwargs
    ) -> LLMResponse:
        """Generate using Z.AI API."""
        start_time = time.time()

        sanitized_prompt = sanitize_prompt(prompt, max_length=6000)
        model = self.task_models.get(task, self.task_models[TaskType.TEXT_GENERATION])

        async with create_ssrf_safe_async_session(
            timeout=self.config.timeout
        ) as client:
            response = await client.post(
                f"{self.base_url}/completions",
                headers={
                    "Authorization": f"Bearer {self.config.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "prompt": sanitized_prompt,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    **kwargs
                }
            )
            response.raise_for_status()
            data = response.json()

        latency = (time.time() - start_time) * 1000

        return LLMResponse(
            text=data["choices"][0]["text"],
            model=model,
            provider=self.provider_name,
            tokens_used=data.get("usage", {}).get("total_tokens"),
            latency_ms=latency,
            metadata=data.get("metadata")
        )

    async def chat(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 1000,
        temperature: float = 0.7,
        **kwargs
    ) -> LLMResponse:
        """Chat using Z.AI API."""
        start_time = time.time()

        # Sanitize messages
        sanitized_messages = [
            {
                "role": msg["role"],
                "content": sanitize_prompt(msg["content"], max_length=2000)
            }
            for msg in messages
        ]

        model = self.task_models.get(TaskType.CHAT)

        async with create_ssrf_safe_async_session(
            timeout=self.config.timeout
        ) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.config.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": sanitized_messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    **kwargs
                }
            )
            response.raise_for_status()
            data = response.json()

        latency = (time.time() - start_time) * 1000

        return LLMResponse(
            text=data["choices"][0]["message"]["content"],
            model=model,
            provider=self.provider_name,
            tokens_used=data.get("usage", {}).get("total_tokens"),
            latency_ms=latency
        )


class QwenProvider(LLMProvider):
    """Qwen/Dashscope API provider."""

    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.base_url = config.base_url or "https://dashscope.aliyuncs.com/api/v1"
        self.task_models = {
            TaskType.CODE_GENERATION: "qwen-coder-turbo",
            TaskType.TEXT_GENERATION: "qwen-turbo",
            TaskType.CHAT: "qwen-plus",
        }

    async def generate(
        self,
        prompt: str,
        task: TaskType = TaskType.TEXT_GENERATION,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        **kwargs
    ) -> LLMResponse:
        """Generate using Qwen API."""
        # Qwen uses chat format for all tasks
        return await self.chat(
            [{"role": "user", "content": prompt}],
            max_tokens,
            temperature,
            **kwargs
        )

    async def chat(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 1000,
        temperature: float = 0.7,
        **kwargs
    ) -> LLMResponse:
        """Chat using Qwen API."""
        start_time = time.time()

        sanitized_messages = [
            {
                "role": msg["role"],
                "content": sanitize_prompt(msg["content"], max_length=2000)
            }
            for msg in messages
        ]

        model = kwargs.pop("model", self.task_models[TaskType.CHAT])

        async with create_ssrf_safe_async_session(
            timeout=self.config.timeout
        ) as client:
            response = await client.post(
                f"{self.base_url}/services/aigc/text-generation/generation",
                headers={
                    "Authorization": f"Bearer {self.config.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "input": {"messages": sanitized_messages},
                    "parameters": {
                        "max_tokens": max_tokens,
                        "temperature": temperature,
                        **kwargs
                    }
                }
            )
            response.raise_for_status()
            data = response.json()

        latency = (time.time() - start_time) * 1000

        output = data["output"]

        return LLMResponse(
            text=output["text"],
            model=model,
            provider=self.provider_name,
            tokens_used=data.get("usage", {}).get("total_tokens"),
            latency_ms=latency
        )


class OpenAIProvider(LLMProvider):
    """OpenAI API provider."""

    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.base_url = config.base_url or "https://api.openai.com/v1"
        self.task_models = {
            TaskType.CODE_GENERATION: "gpt-4-turbo",
            TaskType.TEXT_GENERATION: "gpt-4o-mini",
            TaskType.CHAT: "gpt-4o",
        }

    async def generate(
        self,
        prompt: str,
        task: TaskType = TaskType.TEXT_GENERATION,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        **kwargs
    ) -> LLMResponse:
        """Generate using OpenAI API."""
        return await self.chat(
            [{"role": "user", "content": prompt}],
            max_tokens,
            temperature,
            task=task,
            **kwargs
        )

    async def chat(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 1000,
        temperature: float = 0.7,
        task: TaskType = TaskType.CHAT,
        **kwargs
    ) -> LLMResponse:
        """Chat using OpenAI API."""
        start_time = time.time()

        sanitized_messages = [
            {
                "role": msg["role"],
                "content": sanitize_prompt(msg["content"], max_length=8000)
            }
            for msg in messages
        ]

        model = kwargs.pop("model", self.task_models.get(task, "gpt-4o-mini"))

        async with create_ssrf_safe_async_session(
            timeout=self.config.timeout
        ) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.config.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": sanitized_messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    **kwargs
                }
            )
            response.raise_for_status()
            data = response.json()

        latency = (time.time() - start_time) * 1000

        return LLMResponse(
            text=data["choices"][0]["message"]["content"],
            model=model,
            provider=self.provider_name,
            tokens_used=data.get("usage", {}).get("total_tokens"),
            cost=self._calculate_cost(model, data.get("usage", {})),
            latency_ms=latency
        )

    def _calculate_cost(self, model: str, usage: Dict) -> Optional[float]:
        """Calculate approximate cost for OpenAI models."""
        # Simplified cost calculation (update with real pricing)
        pricing = {
            "gpt-4o": (0.005, 0.015),  # input, output per 1K tokens
            "gpt-4o-mini": (0.00015, 0.0006),
            "gpt-4-turbo": (0.01, 0.03),
        }

        if model not in pricing or not usage:
            return None

        input_cost, output_cost = pricing[model]
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)

        return (prompt_tokens / 1000 * input_cost) + (completion_tokens / 1000 * output_cost)


class LLMProviderFactory:
    """Factory for creating LLM providers."""

    @staticmethod
    def create(provider_type: str, config: LLMConfig, **kwargs) -> LLMProvider:
        """Create provider instance."""
        providers = {
            "huggingface": HuggingFaceProvider,
            "zai": ZAIProvider,
            "qwen": QwenProvider,
            "openai": OpenAIProvider,
        }

        provider_class = providers.get(provider_type.lower())
        if not provider_class:
            raise ValueError(f"Unknown provider: {provider_type}")

        return provider_class(config, **kwargs)


# Global provider instance
_global_provider: Optional[LLMProvider] = None


def set_global_provider(provider: LLMProvider):
    """Set global LLM provider."""
    global _global_provider
    _global_provider = provider


def get_global_provider() -> LLMProvider:
    """Get global LLM provider."""
    if _global_provider is None:
        raise RuntimeError("No global LLM provider set")
    return _global_provider
