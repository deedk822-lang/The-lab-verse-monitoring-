"""
Observable Ollama Agent
Issue Fixed: #10: OpenLIT tracing for LLM calls
"""

import os
import time
import requests
import uuid
from typing import Optional, Dict, Any

from .observability import logger, CostTracker

# OpenLIT for LLM observability
try:
    import openlit
    OPENLIT_AVAILABLE = True
except ImportError:
    OPENLIT_AVAILABLE = False


class OllamaAgent:
    """
    Ollama agent with complete observability

    Features:
    - OpenLIT tracing
    - Structured logging
    - Cost tracking
    - Performance metrics
    """

    def __init__(
        self,
        model: str = "codellama",
        base_url: str = "http://localhost:11434",
        cost_tracker: Optional[CostTracker] = None
    ):
        self.model = model
        self.base_url = base_url
        self.api_url = f"{base_url}/api/generate"
        self.cost_tracker = cost_tracker or CostTracker()

        # Initialize OpenLIT if available
        if OPENLIT_AVAILABLE:
            openlit.init(
                otlp_endpoint=os.getenv("OTLP_ENDPOINT", "http://localhost:4318"),
                application_name="pr-fix-agent"
            )
            logger.info("openlit_initialized")

    def query(
        self,
        prompt: str,
        temperature: float = 0.2,
        timeout: int = 120,
        trace_id: Optional[str] = None
    ) -> str:
        """
        Query with full observability
        """
        trace_id = trace_id or str(uuid.uuid4())
        start_time = time.time()

        # Structured logging - START
        logger.info(
            "llm_query_start",
            model=self.model,
            prompt_length=len(prompt),
            temperature=temperature,
            trace_id=trace_id
        )

        try:
            # OpenLIT tracing wrapper
            if OPENLIT_AVAILABLE:
                response = self._traced_query(prompt, temperature, timeout, trace_id)
            else:
                response = self._raw_query(prompt, temperature, timeout)

            # Calculate duration
            duration = time.time() - start_time

            # Cost tracking
            cost = self.cost_tracker.record_usage(
                model=self.model,
                prompt=prompt,
                response=response,
                metadata={"trace_id": trace_id, "duration": duration}
            )

            # Structured logging - SUCCESS
            logger.info(
                "llm_query_success",
                model=self.model,
                duration=duration,
                response_length=len(response),
                tokens=cost.total_tokens,
                cost=cost.estimated_cost,
                trace_id=trace_id
            )

            return response

        except Exception as e:
            # Structured logging - ERROR
            logger.error(
                "llm_query_failed",
                model=self.model,
                error=str(e),
                error_type=type(e).__name__,
                duration=time.time() - start_time,
                trace_id=trace_id,
                exc_info=True
            )
            raise

    def _traced_query(self, prompt: str, temperature: float, timeout: int, trace_id: str) -> str:
        """Query with OpenLIT tracing"""
        with openlit.trace(
            name="ollama_query",
            kind="llm",
            attributes={
                "llm.model": self.model,
                "llm.temperature": temperature,
                "llm.prompt_length": len(prompt),
                "trace_id": trace_id
            }
        ):
            return self._raw_query(prompt, temperature, timeout)

    def _raw_query(self, prompt: str, temperature: float, timeout: int) -> str:
        """Raw query without tracing"""
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
        return response.json()["response"]
