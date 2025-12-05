"""
LocalAI Fallback Service - Advanced Resilience System
Drop-in OpenAI-compatible local alternative for when cloud APIs fail
Supports LLM inference, embeddings, and autonomous agents
"""

import os
import logging
import time
from typing import Optional, Dict, List, Any, Union
from datetime import datetime
import requests
from functools import wraps

logger = logging.getLogger(__name__)


class CircuitBreaker:
    """
    Circuit breaker pattern to prevent cascading failures
    States: CLOSED (normal), OPEN (failing), HALF_OPEN (testing)
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        timeout: int = 60,
        expected_exception: type = Exception
    ):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.expected_exception = expected_exception
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"

    def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.timeout:
                self.state = "HALF_OPEN"
                logger.info(f"Circuit breaker HALF_OPEN, testing {func.__name__}")
            else:
                raise Exception(f"Circuit breaker OPEN for {func.__name__}")

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise e

    def _on_success(self):
        """Reset on successful call"""
        self.failure_count = 0
        self.state = "CLOSED"

    def _on_failure(self):
        """Handle failure"""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            logger.warning(f"Circuit breaker OPEN after {self.failure_count} failures")


class LocalAIClient:
    """
    LocalAI client - OpenAI-compatible local AI inference
    Supports LLMs, embeddings, and image generation
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8080",
        timeout: int = 30
    ):
        """
        Initialize LocalAI client

        Args:
            base_url: LocalAI server URL
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.available = self._check_availability()

        if self.available:
            logger.info(f"✅ LocalAI available at {self.base_url}")
        else:
            logger.warning(f"⚠️ LocalAI not available at {self.base_url}")

    def _check_availability(self) -> bool:
        """Check if LocalAI server is running"""
        try:
            response = requests.get(
                f"{self.base_url}/v1/models",
                timeout=5
            )
            return response.status_code == 200
        except Exception as e:
            logger.debug(f"LocalAI availability check failed: {e}")
            return False

    def list_models(self) -> List[str]:
        """List available models"""
        if not self.available:
            return []

        try:
            response = requests.get(
                f"{self.base_url}/v1/models",
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            return [model["id"] for model in data.get("data", [])]
        except Exception as e:
            logger.error(f"Error listing models: {e}")
            return []

    def chat_completion(
        self,
        messages: List[Dict],
        model: str = "gpt-3.5-turbo",
        temperature: float = 0.7,
        max_tokens: int = 500,
        **kwargs
    ) -> Dict:
        """
        OpenAI-compatible chat completion

        Args:
            messages: Chat messages
            model: Model name (will use best available)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            Chat completion response
        """
        if not self.available:
            raise Exception("LocalAI not available")

        try:
            response = requests.post(
                f"{self.base_url}/v1/chat/completions",
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    **kwargs
                },
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"LocalAI chat completion error: {e}")
            raise

    def embeddings(
        self,
        texts: Union[str, List[str]],
        model: str = "text-embedding-ada-002"
    ) -> Dict:
        """
        Generate embeddings (OpenAI-compatible)

        Args:
            texts: Text or list of texts
            model: Embedding model name

        Returns:
            Embeddings response
        """
        if not self.available:
            raise Exception("LocalAI not available")

        if isinstance(texts, str):
            texts = [texts]

        try:
            response = requests.post(
                f"{self.base_url}/v1/embeddings",
                json={
                    "model": model,
                    "input": texts
                },
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"LocalAI embeddings error: {e}")
            raise


class ResilientAIService:
    """
    Resilient AI service with intelligent fallback
    Priority: Cloud APIs → LocalAI → Mock mode
    Includes circuit breakers, retry logic, and health monitoring
    """

    def __init__(
        self,
        cohere_key: Optional[str] = None,
        mistral_key: Optional[str] = None,
        localai_url: str = "http://localhost:8080",
        enable_fallback: bool = True
    ):
        """
        Initialize resilient AI service

        Args:
            cohere_key: Cohere API key
            mistral_key: Mistral API key
            localai_url: LocalAI server URL
            enable_fallback: Enable automatic fallback
        """
        self.cohere_key = cohere_key or os.getenv("COHERE_API_KEY")
        self.mistral_key = mistral_key or os.getenv("MISTRAL_API_KEY")
        self.enable_fallback = enable_fallback

        # Initialize providers
        self.providers = {}
        self.circuit_breakers = {}

        # Setup Cohere
        if self.cohere_key:
            try:
                import cohere
                self.providers['cohere'] = cohere.Client(self.cohere_key)
                self.circuit_breakers['cohere'] = CircuitBreaker()
                logger.info("✅ Cohere initialized")
            except Exception as e:
                logger.warning(f"Cohere initialization failed: {e}")

        # Setup Mistral
        if self.mistral_key:
            try:
                from mistralai import Mistral
                self.providers['mistral'] = Mistral(api_key=self.mistral_key)
                self.circuit_breakers['mistral'] = CircuitBreaker()
                logger.info("✅ Mistral initialized")
            except Exception as e:
                logger.warning(f"Mistral initialization failed: {e}")

        # Setup LocalAI (always try)
        if self.enable_fallback:
            self.providers['localai'] = LocalAIClient(base_url=localai_url)
            self.circuit_breakers['localai'] = CircuitBreaker(failure_threshold=3)
            if self.providers['localai'].available:
                logger.info("✅ LocalAI initialized")

        # Determine provider priority
        self.provider_priority = self._determine_priority()
        logger.info(f"Provider priority: {' → '.join(self.provider_priority)}")

    def _determine_priority(self) -> List[str]:
        """Determine provider priority based on availability"""
        priority = []

        # Prefer cloud APIs first
        if 'cohere' in self.providers:
            priority.append('cohere')
        if 'mistral' in self.providers:
            priority.append('mistral')

        # LocalAI as fallback
        if 'localai' in self.providers and self.providers['localai'].available:
            priority.append('localai')

        # Always have mock as final fallback
        priority.append('mock')

        return priority

    def generate_text(
        self,
        prompt: str,
        max_tokens: int = 500,
        temperature: float = 0.7,
        preferred_provider: Optional[str] = None
    ) -> Dict:
        """
        Generate text with intelligent fallback

        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens
            temperature: Sampling temperature
            preferred_provider: Preferred provider (optional)

        Returns:
            Generation result with metadata
        """
        providers = [preferred_provider] if preferred_provider else self.provider_priority

        last_error = None
        for provider in providers:
            if provider == 'mock':
                continue

            try:
                # Use circuit breaker
                breaker = self.circuit_breakers.get(provider)
                if breaker:
                    result = breaker.call(
                        self._generate_with_provider,
                        provider, prompt, max_tokens, temperature
                    )
                else:
                    result = self._generate_with_provider(
                        provider, prompt, max_tokens, temperature
                    )

                result['provider'] = provider
                result['fallback_used'] = provider != providers[0]
                logger.info(f"✅ Generation successful with {provider}")
                return result

            except Exception as e:
                last_error = e
                logger.warning(f"❌ {provider} failed: {e}, trying next provider")
                continue

        # All providers failed
        logger.error(f"All providers failed, last error: {last_error}")
        return self._mock_generation(prompt, error=str(last_error))

    def _generate_with_provider(
        self,
        provider: str,
        prompt: str,
        max_tokens: int,
        temperature: float
    ) -> Dict:
        """Generate text with specific provider"""
        if provider == 'cohere':
            return self._generate_cohere(prompt, max_tokens, temperature)
        elif provider == 'mistral':
            return self._generate_mistral(prompt, max_tokens, temperature)
        elif provider == 'localai':
            return self._generate_localai(prompt, max_tokens, temperature)
        else:
            raise ValueError(f"Unknown provider: {provider}")

    def _generate_cohere(self, prompt: str, max_tokens: int, temperature: float) -> Dict:
        """Generate with Cohere"""
        client = self.providers['cohere']
        response = client.chat(
            message=prompt,
            max_tokens=max_tokens,
            temperature=temperature
        )
        return {
            "text": response.text,
            "usage": {
                "input_tokens": getattr(response.meta, 'billed_units', {}).get('input_tokens', 0),
                "output_tokens": getattr(response.meta, 'billed_units', {}).get('output_tokens', 0)
            }
        }

    def _generate_mistral(self, prompt: str, max_tokens: int, temperature: float) -> Dict:
        """Generate with Mistral"""
        client = self.providers['mistral']
        response = client.chat.complete(
            model="mistral-small-latest",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=temperature
        )
        return {
            "text": response.choices[0].message.content,
            "usage": {
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens
            }
        }

    def _generate_localai(self, prompt: str, max_tokens: int, temperature: float) -> Dict:
        """Generate with LocalAI"""
        client = self.providers['localai']
        response = client.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=temperature
        )
        return {
            "text": response['choices'][0]['message']['content'],
            "usage": response.get('usage', {})
        }

    def _mock_generation(self, prompt: str, error: Optional[str] = None) -> Dict:
        """Mock generation as final fallback"""
        return {
            "text": f"[MOCK] Response to: {prompt[:100]}...",
            "provider": "mock",
            "fallback_used": True,
            "mock": True,
            "error": error,
            "usage": {"input_tokens": 0, "output_tokens": 0}
        }

    def generate_embeddings(
        self,
        texts: List[str],
        preferred_provider: Optional[str] = None
    ) -> Dict:
        """
        Generate embeddings with fallback

        Args:
            texts: List of texts to embed
            preferred_provider: Preferred provider

        Returns:
            Embeddings result
        """
        providers = [preferred_provider] if preferred_provider else self.provider_priority

        for provider in providers:
            if provider == 'mock':
                continue

            try:
                breaker = self.circuit_breakers.get(provider)
                if breaker:
                    result = breaker.call(
                        self._embed_with_provider,
                        provider, texts
                    )
                else:
                    result = self._embed_with_provider(provider, texts)

                result['provider'] = provider
                logger.info(f"✅ Embeddings successful with {provider}")
                return result

            except Exception as e:
                logger.warning(f"❌ {provider} embeddings failed: {e}")
                continue

        # Final fallback
        import numpy as np
        return {
            "embeddings": np.random.rand(len(texts), 384).tolist(),
            "provider": "mock",
            "mock": True
        }

    def _embed_with_provider(self, provider: str, texts: List[str]) -> Dict:
        """Generate embeddings with specific provider"""
        if provider == 'cohere':
            client = self.providers['cohere']
            response = client.embed(
                texts=texts,
                model='embed-english-v3.0',
                input_type="search_document"
            )
            return {"embeddings": response.embeddings}

        elif provider == 'localai':
            client = self.providers['localai']
            response = client.embeddings(texts)
            return {
                "embeddings": [item['embedding'] for item in response['data']]
            }

        else:
            raise ValueError(f"Provider {provider} doesn't support embeddings")

    def get_health_status(self) -> Dict:
        """Get health status of all providers"""
        status = {
            "timestamp": datetime.utcnow().isoformat(),
            "providers": {}
        }

        for name, breaker in self.circuit_breakers.items():
            status["providers"][name] = {
                "available": name in self.providers,
                "circuit_state": breaker.state,
                "failure_count": breaker.failure_count
            }

        status["recommended_provider"] = self.provider_priority[0] if self.provider_priority else None

        return status


class LocalAISetup:
    """Helper class for LocalAI setup and configuration"""

    @staticmethod
    def get_docker_command(
        port: int = 8080,
        models: Optional[List[str]] = None
    ) -> str:
        """
        Generate Docker command to run LocalAI

        Args:
            port: Port to expose
            models: Models to preload

        Returns:
            Docker run command
        """
        cmd = f"docker run -p {port}:8080 --name local-ai -ti localai/localai:latest"

        if models:
            # Add model configuration
            cmd += f" --models {','.join(models)}"

        return cmd

    @staticmethod
    def install_instructions() -> str:
        """Get installation instructions"""
        return """
LocalAI Installation Instructions:

1. Using Docker (Recommended):
   docker run -p 8080:8080 --name local-ai -ti localai/localai:latest

2. With GPU support:
   docker run -p 8080:8080 --gpus all --name local-ai -ti localai/localai:latest-gpu

3. With specific models:
   docker run -p 8080:8080 --name local-ai -e MODELS_PATH=/models \\
     -v $PWD/models:/models localai/localai:latest

4. Kubernetes:
   kubectl apply -f https://raw.githubusercontent.com/go-skynet/LocalAI/master/kubernetes/deployment.yaml

For more information: https://localai.io/basics/getting_started/
"""
