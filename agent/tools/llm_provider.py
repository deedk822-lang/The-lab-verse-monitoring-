"""
Multi-provider LLM abstraction layer with proper HuggingFace token handling.
Fixed: HuggingFace now properly uses HF_TOKEN for authentication.
"""

import asyncio
import logging
import os
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

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
    # HuggingFace specific
    model_path: Optional[str] = None
    device: str = "cpu"
    use_auth_token: bool = True  # Whether to use HF_TOKEN


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
    """
    HuggingFace local model provider with proper token authentication.

    Critical: Uses HF_TOKEN (api_key) for:
    - Downloading models from HuggingFace Hub
    - Accessing gated/private models
    - Higher rate limits
    - Model authentication
    """

    def __init__(self, config: LLMConfig):
        super().__init__(config)

        # Validate token is provided
        self.hf_token = config.api_key
        if not self.hf_token and config.use_auth_token:
            logger.warning(
                "HuggingFace token (HF_TOKEN) not provided. "
                "This may cause issues with:\n"
                "  - Downloading models\n"
                "  - Accessing gated models\n"
                "  - Rate limits\n"
                "Set HF_TOKEN environment variable or pass api_key in config."
            )

        self.task_models = {
            TaskType.CODE_GENERATION: "Qwen/Qwen2.5-Coder-7B-Instruct",
            TaskType.TEXT_GENERATION: "meta-llama/Llama-3.2-3B-Instruct",
            TaskType.CHAT: "meta-llama/Llama-3.2-3B-Instruct",
        }

        # Lazy initialization
        self._model = None
        self._tokenizer = None
        self._device = config.device
        self._model_path = config.model_path or os.path.expanduser("~/.cache/huggingface")
        self._current_model_name = None
        self._use_auth_token = config.use_auth_token

        # Set HuggingFace token in environment for transformers library
        if self.hf_token:
            os.environ['HF_TOKEN'] = self.hf_token
            os.environ['HUGGING_FACE_HUB_TOKEN'] = self.hf_token
            logger.info("HuggingFace token configured for model access")

    def _ensure_model_loaded(self, model_name: str):
        """
        Lazy load model with proper HuggingFace token authentication.

        The token is used for:
        - snapshot_download() to fetch model files
        - AutoTokenizer.from_pretrained() for tokenizer download
        - AutoModelForCausalLM.from_pretrained() for model download
        """
        if self._model is None or self._current_model_name != model_name:
            try:
                import torch
                from transformers import AutoModelForCausalLM, AutoTokenizer

                logger.info(f"Loading HuggingFace model: {model_name}")

                # Determine auth token usage
                use_auth_token = self.hf_token if self._use_auth_token else None

                if use_auth_token:
                    logger.info("Using HuggingFace token for authentication")
                else:
                    logger.warning(
                        "Loading model without authentication. "
                        "This may fail for gated models or hit rate limits."
                    )

                # Load tokenizer with authentication
                logger.debug(f"Loading tokenizer from {model_name}")
                self._tokenizer = AutoTokenizer.from_pretrained(
                    model_name,
                    cache_dir=self._model_path,
                    token=use_auth_token,
                    trust_remote_code=False
                )

                # Load model with authentication
                logger.debug(f"Loading model from {model_name}")
                self._model = AutoModelForCausalLM.from_pretrained(
                    model_name,
                    cache_dir=self._model_path,
                    token=use_auth_token,
                    torch_dtype=torch.float16 if self._device == "cuda" else torch.float32,
                    low_cpu_mem_usage=True,
                    trust_remote_code=False
                )

                # Move to device
                if torch.cuda.is_available() and self._device == "cuda":
                    logger.debug("Moving model to CUDA")
                    self._model = self._model.to("cuda")

                self._current_model_name = model_name
                logger.info(
                    f"HuggingFace model loaded successfully: {model_name} "
                    f"(device: {self._device}, "
                    f"authenticated: {bool(use_auth_token)})"
                )

            except ImportError as e:
                raise RuntimeError(
                    "HuggingFace transformers not installed. "
                    "Install with: pip install transformers torch"
                ) from e

            except OSError as e:
                error_msg = str(e)
                if "401" in error_msg or "403" in error_msg:
                    raise RuntimeError(
                        f"Authentication failed for model {model_name}. "
                        f"This model requires a valid HuggingFace token. "
                        f"Please:\n"
                        f"  1. Get token from https://huggingface.co/settings/tokens\n"
                        f"  2. Set HF_TOKEN environment variable\n"
                        f"  3. Accept model terms if it's a gated model\n"
                        f"Error: {error_msg}"
                    ) from e
                elif "rate limit" in error_msg.lower():
                    raise RuntimeError(
                        f"HuggingFace rate limit exceeded for model {model_name}. "
                        f"Using a token provides higher rate limits. "
                        f"Set HF_TOKEN environment variable."
                    ) from e
                else:
                    raise RuntimeError(
                        f"Failed to load model {model_name}: {error_msg}\n"
                        f"Check:\n"
                        f"  1. Model name is correct\n"
                        f"  2. You have internet connection\n"
                        f"  3. HF_TOKEN is set if model is gated/private\n"
                        f"  4. You have sufficient disk space in {self._model_path}"
                    ) from e

            except Exception as e:
                raise RuntimeError(
                    f"Unexpected error loading model {model_name}: {e}"
                ) from e

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

        # Load model if needed (with token authentication)
        self._ensure_model_loaded(model_name)

        # Generate (synchronous call in executor)
        def _generate():
            inputs = self._tokenizer(
                sanitized_prompt,
                return_tensors="pt",
                truncation=True,
                max_length=4096
            )

            if self._device == "cuda":
                inputs = inputs.to("cuda")

            outputs = self._model.generate(
                **inputs,
                max_new_tokens=max_tokens,
                temperature=temperature,
                do_sample=temperature > 0,
                pad_token_id=self._tokenizer.eos_token_id,
                **kwargs
            )

            return self._tokenizer.decode(outputs[0], skip_special_tokens=True)

        text = await asyncio.get_event_loop().run_in_executor(None, _generate)

        latency = (time.time() - start_time) * 1000

        return LLMResponse(
            text=text,
            model=model_name,
            provider=self.provider_name,
            latency_ms=latency,
            metadata={
                "device": self._device,
                "authenticated": bool(self.hf_token)
            }
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
        pricing = {
            "gpt-4o": (0.005, 0.015),
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
    """Factory for creating LLM providers with proper configuration."""

    @staticmethod
    def create(provider_type: str, config: LLMConfig) -> LLMProvider:
        """
        Create provider instance with proper configuration.

        Args:
            provider_type: Type of provider (huggingface, openai)
            config: LLM configuration with all required parameters

        Returns:
            Configured LLM provider instance

        Raises:
            ValueError: If provider_type is unknown
            RuntimeError: If provider cannot be initialized
        """
        providers = {
            "huggingface": HuggingFaceProvider,
            "openai": OpenAIProvider,
        }

        provider_class = providers.get(provider_type.lower())
        if not provider_class:
            raise ValueError(
                f"Unknown provider: {provider_type}. "
                f"Available: {', '.join(providers.keys())}"
            )

        try:
            return provider_class(config)
        except Exception as e:
            raise RuntimeError(
                f"Failed to initialize {provider_type} provider: {e}"
            ) from e


# Global provider instance
_global_provider: Optional[LLMProvider] = None


def set_global_provider(provider: LLMProvider):
    """Set global LLM provider."""
    global _global_provider
    _global_provider = provider


def get_global_provider() -> LLMProvider:
    """Get global LLM provider."""
    if _global_provider is None:
        raise RuntimeError(
            "No global LLM provider set. "
            "Call set_global_provider() or initialize_from_env() first."
        )
    return _global_provider


def initialize_from_env() -> LLMProvider:
    """
    Initialize provider from environment variables.

    Environment Variables:
        LLM_PROVIDER: Provider type (huggingface, openai)

        For HuggingFace:
            HF_TOKEN: HuggingFace API token (REQUIRED for most models)
            HF_MODEL_PATH: Model cache directory (optional)
            HF_DEVICE: Device to use (cpu, cuda) (optional)

        For OpenAI:
            OPENAI_API_KEY: OpenAI API key (REQUIRED)
            OPENAI_BASE_URL: OpenAI base URL (optional)

    Returns:
        Configured provider instance

    Raises:
        RuntimeError: If required environment variables are missing
    """
    provider_type = os.getenv('LLM_PROVIDER', 'openai')

    # Build config based on provider type
    if provider_type == 'huggingface':
        hf_token = os.getenv('HF_TOKEN')
        if not hf_token:
            logger.warning(
                "HF_TOKEN not set. HuggingFace provider will work but:\n"
                "  - Cannot download models that require authentication\n"
                "  - Lower rate limits apply\n"
                "  - Gated models will fail\n"
                "Get your token from: https://huggingface.co/settings/tokens"
            )

        config = LLMConfig(
            api_key=hf_token,
            model_path=os.getenv('HF_MODEL_PATH', os.path.expanduser('~/.cache/huggingface')),
            device=os.getenv('HF_DEVICE', 'cpu'),
            use_auth_token=True
        )
    elif provider_type == 'openai':
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise RuntimeError(
                "OPENAI_API_KEY environment variable required for OpenAI provider"
            )
        config = LLMConfig(
            api_key=api_key,
            base_url=os.getenv('OPENAI_BASE_URL'),
            timeout=float(os.getenv('OPENAI_TIMEOUT', '60'))
        )
    else:
        raise RuntimeError(f"Unsupported provider type: {provider_type}")

    provider = LLMProviderFactory.create(provider_type, config)
    set_global_provider(provider)

    logger.info(f"Initialized {provider_type} provider")
    return provider
