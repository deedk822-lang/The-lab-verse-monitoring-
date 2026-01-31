<<<<<<< HEAD
import os
import json
import requests
import structlog
from typing import Optional, Dict, Any

from pr_fix_agent.security.secure_requests import create_ssrf_safe_requests_session

logger = structlog.get_logger(__name__)
=======
"""
Unified OllamaAgent - Canonical Implementation
FIXES: Multiple conflicting OllamaAgent implementations
CONSOLIDATES: ollama_agent.py and observability.py versions
"""

import os
import threading
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests
import structlog

logger = structlog.get_logger()
>>>>>>> main

# Try to import OpenLIT for observability
try:
    import openlit
    OPENLIT_AVAILABLE = True
except ImportError:
    OPENLIT_AVAILABLE = False
    logger.warning("openlit_not_available", message="Install openlit for LLM tracing")

<<<<<<< HEAD
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
=======

# ============================================================================
# Cost Tracking & Budget Enforcement
# ============================================================================

@dataclass
class LLMCost:
    """Track single LLM invocation cost"""
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_cost: float
    timestamp: str

    def to_dict(self) -> dict:
        return asdict(self)


class CostTracker:
    """
    Track and enforce LLM usage budgets

    Thread-safe implementation
    """

    # Cost per 1M tokens (approximate for Ollama - adjust for your setup)
    MODEL_COSTS = {
        "deepseek-r1:14b": 0.0,  # Free (local)
        "qwen2.5-coder:32b": 0.0,  # Free (local)
        "codellama:34b": 0.0,  # Free (local)
        "gpt-4": 30.0,
        "claude-3": 15.0,
    }

    def __init__(self, budget_usd: float = 10.0):
        self.budget_usd = budget_usd
        self.total_cost = 0.0
        self.costs: List[LLMCost] = []
        self._lock = threading.Lock()

    def record_usage(
        self,
        model: str,
        prompt: str,
        response: str
    ) -> LLMCost:
        """Record usage with cost calculation"""

        # Estimate tokens (rough approximation: 1 token ≈ 4 chars)
        prompt_tokens = len(prompt) // 4
        completion_tokens = len(response) // 4
        total_tokens = prompt_tokens + completion_tokens

        # Calculate cost
        cost_per_million = self.MODEL_COSTS.get(model, 0.0)
        estimated_cost = (total_tokens / 1_000_000) * cost_per_million

        cost = LLMCost(
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            estimated_cost=estimated_cost,
            timestamp=datetime.utcnow().isoformat()
        )

        with self._lock:
            self.costs.append(cost)
            self.total_cost += estimated_cost

            if self.total_cost > self.budget_usd:
                logger.warning(
                    "budget_exceeded",
                    total_cost=self.total_cost,
                    budget=self.budget_usd
                )
                raise BudgetExceededError(
                    f"Budget exceeded: ${self.total_cost:.2f} > ${self.budget_usd:.2f}"
                )

        logger.info(
            "llm_cost_recorded",
            model=model,
            tokens=total_tokens,
            cost=estimated_cost
        )

        return cost

    def get_report(self) -> Dict[str, Any]:
        """Generate usage report"""
        with self._lock:
            if not self.costs:
                return {
                    "total_calls": 0,
                    "total_tokens": 0,
                    "total_cost": 0.0,
                    "budget_remaining": self.budget_usd
                }

            total_tokens = sum(c.total_tokens for c in self.costs)

            by_model: Dict[str, Dict[str, Any]] = {}
            for cost in self.costs:
                if cost.model not in by_model:
                    by_model[cost.model] = {
                        "calls": 0,
                        "tokens": 0,
                        "cost": 0.0
                    }
                by_model[cost.model]["calls"] += 1
                by_model[cost.model]["tokens"] += cost.total_tokens
                by_model[cost.model]["cost"] += cost.estimated_cost

            return {
                "total_calls": len(self.costs),
                "total_tokens": total_tokens,
                "total_cost": self.total_cost,
                "budget_limit": self.budget_usd,
                "budget_remaining": self.budget_usd - self.total_cost,
                "usage_by_model": by_model
            }


class BudgetExceededError(Exception):
    """Raised when budget limit is exceeded"""
    pass

class OllamaQueryError(Exception):
    """Raised when Ollama query fails"""
    pass


# ============================================================================
# Canonical OllamaAgent
# ============================================================================

class OllamaAgent:
    """
    Canonical Production Ollama Agent

    Features:
    - ✅ OpenLIT tracing for LLM calls
    - ✅ Structured logging
    - ✅ Cost tracking & budget enforcement
    - ✅ Proper error handling (raises exceptions)
    - ✅ Thread-safe
    """
>>>>>>> main

    def __init__(
        self,
        model: str = "codellama",
        base_url: str = "http://localhost:11434",
<<<<<<< HEAD
        cost_tracker: Optional[Any] = None
=======
        cost_tracker: Optional[CostTracker] = None
>>>>>>> main
    ):
        self.model = model
        self.base_url = base_url
        self.api_url = f"{base_url}/api/generate"
<<<<<<< HEAD
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
=======
        self.cost_tracker = cost_tracker or CostTracker()

        # Initialize OpenLIT if available
        if OPENLIT_AVAILABLE:
            try:
                openlit.init(
                    otlp_endpoint=os.getenv("OTLP_ENDPOINT", "http://localhost:4318"),
                    application_name="pr-fix-agent"
                )
                logger.info("openlit_initialized")
            except Exception as e:
                logger.warning("openlit_init_failed", error=str(e))
>>>>>>> main

    def query(
        self,
        prompt: str,
<<<<<<< HEAD
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
=======
        temperature: float = 0.2,
        timeout: int = 120,
        trace_id: Optional[str] = None
    ) -> str:
        """Query with full observability and tracing"""
        start_time = time.time()
        trace_id = trace_id or str(time.time())

        logger.info(
            "ollama_query_start",
            model=self.model,
            prompt_length=len(prompt),
            trace_id=trace_id
        )

        try:
            if OPENLIT_AVAILABLE:
                with openlit.trace(
                    name="ollama_query",
                    kind="llm",
                    attributes={
                        "llm.model": self.model,
                        "llm.temperature": temperature,
                        "trace_id": trace_id
                    }
                ):
                    response_text = self._make_request(prompt, temperature, timeout)
            else:
                response_text = self._make_request(prompt, temperature, timeout)

            duration = time.time() - start_time

            # Record usage
            self.cost_tracker.record_usage(
                model=self.model,
                prompt=prompt,
                response=response_text
            )
>>>>>>> main

            logger.info(
                "ollama_query_success",
                model=self.model,
<<<<<<< HEAD
                response_length=len(result),
                prompt_tokens=data.get("prompt_eval_count", 0),
                completion_tokens=data.get("eval_count", 0)
            )

            return result

        except requests.exceptions.RequestException as e:
=======
                duration=duration,
                response_length=len(response_text)
            )

            return response_text

        except Exception as e:
>>>>>>> main
            logger.error(
                "ollama_query_failed",
                model=self.model,
                error=str(e),
<<<<<<< HEAD
                error_type=type(e).__name__
            )
            raise
=======
                duration=time.time() - start_time
            )
            if isinstance(e, (BudgetExceededError, OllamaQueryError)):
                raise
            raise OllamaQueryError(str(e)) from e

    def _make_request(self, prompt: str, temperature: float, timeout: int) -> str:
        """Make HTTP request to Ollama"""
        response = requests.post(
            self.api_url,
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "temperature": temperature
            },
            timeout=timeout
        )
        response.raise_for_status()
        data = response.json()

        if "response" not in data:
            raise OllamaQueryError(f"Invalid response format: {data}")

        return data["response"]


class MockOllamaAgent:
    """Mock Ollama agent for testing"""

    def __init__(self, model: str = "test"):
        self.model = model
        self.queries: List[str] = []
        self.responses: Dict[str, str] = {}

    def query(self, prompt: str, **kwargs) -> str:
        self.queries.append(prompt)
        for key, response in self.responses.items():
            if key in prompt:
                return response
        return "Mock response"

    def set_response(self, key: str, response: str):
        self.responses[key] = response
>>>>>>> main
