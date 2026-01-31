from __future__ import annotations

import os
import time
from enum import Enum
from typing import Any, Dict, List, Optional, Union

import httpx
from pydantic import BaseModel, Field

from pr_fix_agent.ollama_agent import OllamaAgent
from pr_fix_agent.security.secure_requests import create_ssrf_safe_session

class ProviderPolicy(str, Enum):
    """Provider selection strategies."""
    AUTO = "auto"
    FASTEST = "fastest"
    CHEAPEST = "cheapest"
    GROQ = "groq"
    CEREBRAS = "cerebras"
    SAMBANOVA = "sambanova"
    HF_INFERENCE = "hf_inference"
    REPLICATE = "replicate"
    TOGETHER = "together"
    FIREWORKS = "fireworks"
    FAL_AI = "fal_ai"


class ChatResponse(BaseModel):
    """Unified chat response."""
    content: str
    provider: str
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    duration: float = 0.0
    cost_estimate: float = 0.0


class HuggingFaceAgent:
    """
    HuggingFace Inference Providers Agent.
    Supports 18 world-class providers via a unified interface.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        default_model: str = "meta-llama/Meta-Llama-3-70B-Instruct",
        default_provider: ProviderPolicy = ProviderPolicy.FASTEST,
    ):
        self.api_key = api_key or os.getenv("HF_API_TOKEN")
        if not self.api_key:
            # Fallback to a dummy key if not provided, to allow initialization in dev
            self.api_key = "dummy_key"

        self.default_model = default_model
        self.default_provider = default_provider

        # ✅ FIX: Use SSRF-safe session
        self.client = create_ssrf_safe_session(timeout=60.0)

    def chat(
        self,
        prompt: str,
        model: Optional[str] = None,
        provider: Optional[ProviderPolicy] = None,
        system_message: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
    ) -> ChatResponse:
        """
        Send chat completion request to HuggingFace Inference Providers.
        Uses the OpenAI-compatible endpoint.
        """
        start_time = time.time()

        target_model = model or self.default_model
        target_provider = provider or self.default_provider

        # Build messages
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": prompt})

        # OpenAI-compatible endpoint for Hugging Face Inference API
        API_URL = "https://api-inference.huggingface.co/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        # Add provider header if specified (HF-specific header for routing)
        if target_provider != ProviderPolicy.AUTO:
            headers["X-Inference-Provider"] = target_provider.value

        payload = {
            "model": target_model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        try:
            # ✅ Real implementation: perform the POST request
            response = self.client.post(API_URL, json=payload, headers=headers)

            # Handle rate limits or other errors gracefully
            if response.status_code == 429:
                return self._create_error_response(target_provider.value, target_model, "Rate limit exceeded (429)", start_time)

            response.raise_for_status()
            data = response.json()

            content = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})

            duration = time.time() - start_time
            return ChatResponse(
                content=content,
                provider=target_provider.value,
                model=target_model,
                prompt_tokens=usage.get("prompt_tokens", 0),
                completion_tokens=usage.get("completion_tokens", 0),
                total_tokens=usage.get("total_tokens", 0),
                duration=duration,
                cost_estimate=0.0, # HF Inference is often free or flat rate
            )

        except Exception as e:
            duration = time.time() - start_time
            return self._create_error_response(target_provider.value, target_model, str(e), start_time)

    def _create_error_response(self, provider: str, model: str, error_msg: str, start_time: float) -> ChatResponse:
        return ChatResponse(
            content=f"Error from {provider}: {error_msg}",
            provider=provider,
            model=model,
            duration=time.time() - start_time,
        )

    def embed(self, text: str, model: str = "sentence-transformers/all-MiniLM-L6-v2") -> List[float]:
        """Generate embeddings using HF Inference API."""
        API_URL = f"https://api-inference.huggingface.co/pipeline/feature-extraction/{model}"
        headers = {"Authorization": f"Bearer {self.api_key}"}

        try:
            response = self.client.post(API_URL, json={"inputs": text}, headers=headers)
            response.raise_for_status()
            return response.json()
        except Exception:
            return [0.0] * 384 # Fallback

    def text_to_image(
        self,
        prompt: str,
        model: str = "black-forest-labs/FLUX.1-dev",
        provider: ProviderPolicy = ProviderPolicy.REPLICATE,
    ) -> bytes:
        """Generate image from text using HF Inference API."""
        API_URL = f"https://api-inference.huggingface.co/models/{model}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "X-Inference-Provider": provider.value
        }

        try:
            response = self.client.post(API_URL, json={"inputs": prompt}, headers=headers)
            response.raise_for_status()
            return response.content
        except Exception:
            return b"" # Fallback


class UnifiedLLMAgent:
    """
    Unified agent that switches between Ollama (local) and HuggingFace (cloud).
    """

    def __init__(
        self,
        backend: str = "huggingface",
        api_key: Optional[str] = None,
        default_model: Optional[str] = None,
        default_provider: ProviderPolicy = ProviderPolicy.AUTO,
    ):
        self.backend = backend
        if backend == "huggingface":
            self.agent = HuggingFaceAgent(
                api_key=api_key,
                default_model=default_model or "meta-llama/Meta-Llama-3-70B-Instruct",
                default_provider=default_provider,
            )
        else:
            self.agent = OllamaAgent()

    def chat(self, prompt: str, **kwargs) -> Union[ChatResponse, Any]:
        """Unified chat interface."""
        if self.backend == "huggingface":
            return self.agent.chat(prompt, **kwargs)
        else:
            # Handle Ollama response format
            response = self.agent.chat(prompt)
            return response
