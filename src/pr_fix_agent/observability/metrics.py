"""
Observability components - logging, metrics, and tracing
"""

import time
from contextlib import asynccontextmanager
from typing import Any, Dict, Optional

import structlog
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from prometheus_client import Counter, Gauge, Histogram, start_http_server

from ..core.config import settings


def configure_structured_logging():
    """Configure structured logging"""
    shared_processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    if settings.observability.log_format == "json":
        shared_processors.append(structlog.processors.JSONRenderer())
    else:
        shared_processors.append(structlog.processors.KeyValueRenderer())

    structlog.configure(
        processors=shared_processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def setup_tracing():
    """Setup OpenTelemetry tracing"""
    if not settings.observability.enable_tracing:
        return

    trace.set_tracer_provider(TracerProvider())
    tracer_provider = trace.get_tracer_provider()

    if settings.observability.otlp_endpoint:
        otlp_exporter = OTLPSpanExporter(
            endpoint=settings.observability.otlp_endpoint,
            insecure=True,  # Configure appropriately for production
        )
        span_processor = BatchSpanProcessor(otlp_exporter)
        tracer_provider.add_span_processor(span_processor)


def setup_metrics():
    """Setup Prometheus metrics"""
    if not settings.observability.enable_metrics:
        return

    # Start metrics server
    start_http_server(settings.observability.metrics_port)


# Prometheus metrics
REQUEST_COUNT = Counter(
    "pr_fix_agent_requests_total",
    "Total number of requests",
    ["method", "endpoint", "status_code"],
)

REQUEST_LATENCY = Histogram(
    "pr_fix_agent_request_duration_seconds",
    "Request duration in seconds",
    ["method", "endpoint"],
)

ACTIVE_CONNECTIONS = Gauge(
    "pr_fix_agent_active_connections",
    "Number of active connections",
)

LLM_TOKENS_USED = Counter(
    "pr_fix_agent_llm_tokens_total",
    "Total number of LLM tokens used",
    ["provider", "model"],
)

LLM_COST = Counter(
    "pr_fix_agent_llm_cost_total",
    "Total LLM cost in USD",
    ["provider", "model"],
)


class BudgetExceededError(Exception):
    """Exception raised when budget is exceeded"""
    pass


class LLMCost(BaseModel):
    """LLM cost tracking"""

    provider: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0

    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


class CostTracker:
    """Track LLM costs and enforce budgets"""

    # Cost per 1K tokens (approximate, update with actual pricing)
    COST_RATES = {
        "openai": {
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-3.5-turbo": {"input": 0.0015, "output": 0.002},
        },
        "cohere": {
            "command": {"input": 0.015, "output": 0.015},
        },
        "huggingface": {
            "microsoft/DialoGPT-medium": {"input": 0.0, "output": 0.0},  # Free tier
        },
        "ollama": {
            "codellama:7b-instruct": {"input": 0.0, "output": 0.0},  # Local
        },
    }

    def __init__(self):
        self.daily_budget = settings.llm.cost_budget_daily
        self.costs_today = 0.0

    def calculate_cost(self, provider: str, model: str, input_tokens: int, output_tokens: int) -> LLMCost:
        """Calculate cost for LLM usage"""
        rates = self.COST_RATES.get(provider, {}).get(model, {"input": 0.0, "output": 0.0})

        input_cost = (input_tokens / 1000) * rates.get("input", 0.0)
        output_cost = (output_tokens / 1000) * rates.get("output", 0.0)
        total_cost = input_cost + output_cost

        return LLMCost(
            provider=provider,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=total_cost,
        )

    def check_budget(self, cost: float) -> bool:
        """Check if cost fits within budget"""
        if not settings.llm.enable_cost_tracking:
            return True

        return (self.costs_today + cost) <= self.daily_budget

    def record_cost(self, cost: LLMCost):
        """Record cost usage"""
        if not settings.llm.enable_cost_tracking:
            return

        self.costs_today += cost.cost_usd

        # Update Prometheus metrics
        LLM_TOKENS_USED.labels(
            provider=cost.provider,
            model=cost.model,
        ).inc(cost.total_tokens())

        LLM_COST.labels(
            provider=cost.provider,
            model=cost.model,
        ).inc(cost.cost_usd)

        # Check budget
        if self.costs_today > self.daily_budget:
            raise BudgetExceededError(
                f"Daily budget exceeded: ${self.costs_today:.2f} > ${self.daily_budget:.2f}"
            )


@asynccontextmanager
async def lifespan_metrics():
    """FastAPI lifespan context manager for metrics"""
    if settings.observability.enable_metrics:
        setup_metrics()
    yield