import os
import json
import requests
import structlog
from typing import Optional, Dict, Any

from pr_fix_agent.security.secure_requests import create_ssrf_safe_requests_session

logger = structlog.get_logger(__name__)

# Try to import OpenLIT for observability
try:
    import openlit
    OPENLIT_AVAILABLE = True
except ImportError:
    OPENLIT_AVAILABLE = False
    logger.warning("openlit_not_available", message="Install openlit for LLM tracing")

# Module-level OpenLIT initialization guard
_openlit_initialized = False

if OPENLIT_AVAILABLE and not _openlit_initialized:
    try:
        openlit.init(
            otlp_endpoint=os.getenv("OTLP_ENDPOINT", "http://localhost:4318"),
            application_name="pr-fix-agent"
        )
        logger.info("openlit_initialized")
        _openlit_initialized = True
    except Exception as e:
        logger.warning("openlit_init_failed", error=str(e))


class OllamaAgent:
    """LLM agent using Ollama with observability"""

    def __init__(
        self,
        model: str = "codellama",
        base_url: str = "http://localhost:11434",
        cost_tracker: Optional[Any] = None
    ):
        self.model = model
        self.base_url = base_url
        self.api_url = f"{base_url}/api/generate"
        self.cost_tracker = cost_tracker
        self._mock_responses: Dict[str, str] = {}

        # ✅ FIX: Use SSRF-safe session (allowing localhost for Ollama by default)
        self.session = create_ssrf_safe_requests_session(allowed_domains={"localhost", "127.0.0.1"})

        logger.info(
            "ollama_agent_created",
            model=model,
            base_url=base_url,
            cost_tracking=cost_tracker is not None
        )

    def set_response(self, prompt_prefix: str, response: str):
        """Set a mock response for testing"""
        self._mock_responses[prompt_prefix] = response

    def query(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> str:
        """Query the Ollama model"""
        # Check for mock responses
        for prefix, mock_resp in self._mock_responses.items():
            if prompt.startswith(prefix):
                return mock_resp

        logger.debug(
            "ollama_query_start",
            model=self.model,
            prompt_length=len(prompt),
            temperature=temperature,
            max_tokens=max_tokens
        )

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }

        if system:
            payload["system"] = system

        try:
            response = self.session.post(
                self.api_url,
                json=payload,
                timeout=120
            )
            response.raise_for_status()

            data = response.json()

            if "response" not in data:
                logger.error(
                    "ollama_unexpected_response",
                    available_keys=list(data.keys()),
                    model=self.model
                )
                raise ValueError(f"Unexpected API response format: {list(data.keys())}")

            result = data["response"]

            if self.cost_tracker and "eval_count" in data:
                prompt_tokens = data.get("prompt_eval_count", 0)
                completion_tokens = data.get("eval_count", 0)

                self.cost_tracker.track(
                    model=self.model,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens
                )

            logger.info(
                "ollama_query_success",
                model=self.model,
                response_length=len(result),
                prompt_tokens=data.get("prompt_eval_count", 0),
                completion_tokens=data.get("eval_count", 0)
            )

            return result

        except requests.exceptions.RequestException as e:
            logger.error(
                "ollama_query_failed",
                model=self.model,
                error=str(e),
                error_type=type(e).__name__
            )
            raise
