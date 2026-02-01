"""
Multi-provider LLM agents
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

import httpx
from pydantic import BaseModel, Field

from ..core.config import settings
from ..observability.metrics import CostTracker, LLMCost


class LLMResponse(BaseModel):
    """Standardized LLM response"""

    content: str
    provider: str
    model: str
    cost: LLMCost
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BaseAgent(ABC):
    """Base class for LLM agents"""

    def __init__(self, cost_tracker: Optional[CostTracker] = None):
        self.cost_tracker = cost_tracker or CostTracker()
        self.client = httpx.AsyncClient(timeout=30.0)

    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate response from LLM"""
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()


class ObservableOllamaAgent(BaseAgent):
    """Ollama-based LLM agent with observability"""

    def __init__(self, cost_tracker: Optional[CostTracker] = None):
        super().__init__(cost_tracker)
        self.base_url = settings.llm.ollama_base_url
        self.model = settings.llm.ollama_model

    async def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate response using Ollama"""
        try:
            response = await self.client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    **kwargs,
                },
            )
            response.raise_for_status()
            data = response.json()

            content = data.get("response", "")
            eval_count = data.get("eval_count", 0)
            eval_duration = data.get("eval_duration", 0)

            # Estimate tokens (rough approximation)
            input_tokens = len(prompt.split()) * 1.3  # Rough token estimation
            output_tokens = len(content.split()) * 1.3

            cost = self.cost_tracker.calculate_cost(
                "ollama", self.model, int(input_tokens), int(output_tokens)
            )

            return LLMResponse(
                content=content,
                provider="ollama",
                model=self.model,
                cost=cost,
                metadata={
                    "eval_count": eval_count,
                    "eval_duration": eval_duration,
                    "input_tokens_est": input_tokens,
                    "output_tokens_est": output_tokens,
                },
            )

        except Exception as e:
            raise RuntimeError(f"Ollama generation failed: {e}")


class OpenAIAgent(BaseAgent):
    """OpenAI API agent"""

    def __init__(self, cost_tracker: Optional[CostTracker] = None):
        super().__init__(cost_tracker)
        self.api_key = settings.llm.openai_api_key
        self.base_url = settings.llm.openai_base_url or "https://api.openai.com/v1"
        self.model = "gpt-4"  # Default model

    async def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate response using OpenAI"""
        if not self.api_key:
            raise RuntimeError("OpenAI API key not configured")

        try:
            response = await self.client.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": kwargs.get("model", self.model),
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": kwargs.get("temperature", 0.7),
                },
            )
            response.raise_for_status()
            data = response.json()

            choice = data["choices"][0]
            content = choice["message"]["content"]
            usage = data.get("usage", {})

            input_tokens = usage.get("prompt_tokens", 0)
            output_tokens = usage.get("completion_tokens", 0)

            cost = self.cost_tracker.calculate_cost(
                "openai", self.model, input_tokens, output_tokens
            )

            return LLMResponse(
                content=content,
                provider="openai",
                model=self.model,
                cost=cost,
                metadata={
                    "usage": usage,
                    "finish_reason": choice.get("finish_reason"),
                },
            )

        except Exception as e:
            raise RuntimeError(f"OpenAI generation failed: {e}")


class CohereAgent(BaseAgent):
    """Cohere API agent"""

    def __init__(self, cost_tracker: Optional[CostTracker] = None):
        super().__init__(cost_tracker)
        self.api_key = settings.llm.cohere_api_key
        self.model = "command"  # Default model

    async def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate response using Cohere"""
        if not self.api_key:
            raise RuntimeError("Cohere API key not configured")

        try:
            response = await self.client.post(
                "https://api.cohere.ai/v1/generate",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": kwargs.get("model", self.model),
                    "prompt": prompt,
                    "max_tokens": kwargs.get("max_tokens", 1000),
                    "temperature": kwargs.get("temperature", 0.7),
                },
            )
            response.raise_for_status()
            data = response.json()

            content = data.get("text", "")
            meta = data.get("meta", {})
            tokens = meta.get("tokens", {})

            input_tokens = tokens.get("input_tokens", 0)
            output_tokens = tokens.get("output_tokens", 0)

            cost = self.cost_tracker.calculate_cost(
                "cohere", self.model, input_tokens, output_tokens
            )

            return LLMResponse(
                content=content,
                provider="cohere",
                model=self.model,
                cost=cost,
                metadata={
                    "meta": meta,
                    "tokens": tokens,
                },
            )

        except Exception as e:
            raise RuntimeError(f"Cohere generation failed: {e}")


class HuggingFaceAgent(BaseAgent):
    """HuggingFace API agent"""

    def __init__(self, cost_tracker: Optional[CostTracker] = None):
        super().__init__(cost_tracker)
        self.api_key = settings.llm.huggingface_api_key
        self.model = settings.llm.huggingface_model

    async def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate response using HuggingFace"""
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}

        try:
            response = await self.client.post(
                f"https://api-inference.huggingface.co/models/{self.model}",
                headers=headers,
                json={
                    "inputs": prompt,
                    "parameters": {
                        "max_new_tokens": kwargs.get("max_tokens", 1000),
                        "temperature": kwargs.get("temperature", 0.7),
                    },
                },
            )
            response.raise_for_status()
            data = response.json()

            # Handle different response formats
            if isinstance(data, list) and data:
                content = data[0].get("generated_text", "")
            else:
                content = str(data)

            # Estimate tokens (rough approximation)
            input_tokens = len(prompt.split()) * 1.3
            output_tokens = len(content.split()) * 1.3

            cost = self.cost_tracker.calculate_cost(
                "huggingface", self.model, int(input_tokens), int(output_tokens)
            )

            return LLMResponse(
                content=content,
                provider="huggingface",
                model=self.model,
                cost=cost,
                metadata={
                    "input_tokens_est": input_tokens,
                    "output_tokens_est": output_tokens,
                },
            )

        except Exception as e:
            raise RuntimeError(f"HuggingFace generation failed: {e}")


class AgentFactory:
    """Factory for creating LLM agents"""

    @staticmethod
    def create_agent(provider: str, cost_tracker: Optional[CostTracker] = None) -> BaseAgent:
        """Create agent instance for specified provider"""
        providers = {
            "ollama": ObservableOllamaAgent,
            "openai": OpenAIAgent,
            "cohere": CohereAgent,
            "huggingface": HuggingFaceAgent,
        }

        agent_class = providers.get(provider.lower())
        if not agent_class:
            raise ValueError(f"Unsupported provider: {provider}")

        return agent_class(cost_tracker)