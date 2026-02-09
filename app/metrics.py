"""
Prometheus metrics for VAAL AI Empire monitoring.
Tracks LLM usage, performance, security events, and system health.
"""

import logging
import time
from functools import wraps
from typing import Callable, Optional

from fastapi import Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    REGISTRY,
    Counter,
    Gauge,
    Histogram,
    Info,
    Summary,
    generate_latest,
)

logger = logging.getLogger(__name__)

# ============================================================================
# Request Metrics
# ============================================================================

http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0]
)

http_request_size_bytes = Summary(
    'http_request_size_bytes',
    'HTTP request size in bytes',
    ['method', 'endpoint']
)

http_response_size_bytes = Summary(
    'http_response_size_bytes',
    'HTTP response size in bytes',
    ['method', 'endpoint']
)

# ============================================================================
# LLM Provider Metrics
# ============================================================================

llm_requests_total = Counter(
    'llm_requests_total',
    'Total LLM requests',
    ['provider', 'model', 'task', 'status']
)

llm_request_duration_seconds = Histogram(
    'llm_request_duration_seconds',
    'LLM request duration',
    ['provider', 'model', 'task'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0]
)

llm_tokens_used = Counter(
    'llm_tokens_used_total',
    'Total tokens used',
    ['provider', 'model', 'task', 'type']  # type: prompt, completion
)

llm_cost = Counter(
    'llm_cost_usd_total',
    'Total LLM cost in USD',
    ['provider', 'model', 'task']
)

llm_errors_total = Counter(
    'llm_errors_total',
    'Total LLM errors',
    ['provider', 'model', 'error_type']
)

llm_active_requests = Gauge(
    'llm_active_requests',
    'Currently active LLM requests',
    ['provider', 'model']
)

# ============================================================================
# Security Metrics
# ============================================================================

security_events_total = Counter(
    'security_events_total',
    'Total security events',
    ['event_type', 'severity', 'blocked']
)

prompt_injections_detected = Counter(
    'prompt_injections_detected_total',
    'Prompt injection attempts detected',
    ['pattern', 'blocked']
)

ssrf_attempts_blocked = Counter(
    'ssrf_attempts_blocked_total',
    'SSRF attempts blocked',
    ['reason']
)

rate_limit_exceeded = Counter(
    'rate_limit_exceeded_total',
    'Rate limit violations',
    ['client_id', 'endpoint']
)

authentication_failures = Counter(
    'authentication_failures_total',
    'Authentication failures',
    ['reason']
)

# ============================================================================
# Webhook Metrics
# ============================================================================

webhook_events_total = Counter(
    'webhook_events_total',
    'Total webhook events received',
    ['source', 'event_type', 'status']
)

webhook_processing_duration_seconds = Histogram(
    'webhook_processing_duration_seconds',
    'Webhook processing duration',
    ['source', 'event_type'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0]
)

webhook_duplicates_detected = Counter(
    'webhook_duplicates_detected_total',
    'Duplicate webhooks detected',
    ['source']
)

webhook_forward_errors = Counter(
    'webhook_forward_errors_total',
    'Webhook forwarding errors',
    ['source', 'error_type']
)

# ============================================================================
# Database Metrics
# ============================================================================

db_connections_active = Gauge(
    'db_connections_active',
    'Active database connections'
)

db_query_duration_seconds = Histogram(
    'db_query_duration_seconds',
    'Database query duration',
    ['operation'],
    buckets=[0.001, 0.01, 0.05, 0.1, 0.5, 1.0, 2.0]
)

db_errors_total = Counter(
    'db_errors_total',
    'Database errors',
    ['operation', 'error_type']
)

# ============================================================================
# Cache Metrics
# ============================================================================

cache_hits_total = Counter(
    'cache_hits_total',
    'Cache hits',
    ['cache_name']
)

cache_misses_total = Counter(
    'cache_misses_total',
    'Cache misses',
    ['cache_name']
)

cache_size_bytes = Gauge(
    'cache_size_bytes',
    'Cache size in bytes',
    ['cache_name']
)

# ============================================================================
# System Metrics
# ============================================================================

system_info = Info(
    'system_info',
    'System information'
)

gpu_memory_used_bytes = Gauge(
    'gpu_memory_used_bytes',
    'GPU memory used',
    ['device']
)

gpu_utilization_percent = Gauge(
    'gpu_utilization_percent',
    'GPU utilization percentage',
    ['device']
)

# ============================================================================
# Business Metrics
# ============================================================================

user_requests_total = Counter(
    'user_requests_total',
    'Total user requests',
    ['user_id', 'endpoint']
)

user_cost_total = Counter(
    'user_cost_usd_total',
    'Total user cost in USD',
    ['user_id']
)

active_users = Gauge(
    'active_users',
    'Currently active users'
)

# ============================================================================
# Helper Functions and Decorators
# ============================================================================

def track_time(metric: Histogram, labels: Optional[dict] = None):
    """Decorator to track execution time."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                if labels:
                    metric.labels(**labels).observe(duration)
                else:
                    metric.observe(duration)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                if labels:
                    metric.labels(**labels).observe(duration)
                else:
                    metric.observe(duration)

        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def track_llm_request(provider: str, model: str, task: str):
    """Context manager to track LLM request metrics."""
    class LLMRequestTracker:
        def __init__(self, provider: str, model: str, task: str):
            self.provider = provider
            self.model = model
            self.task = task
            self.start_time = None

        def __enter__(self):
            self.start_time = time.time()
            llm_active_requests.labels(
                provider=self.provider,
                model=self.model
            ).inc()
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            duration = time.time() - self.start_time

            llm_active_requests.labels(
                provider=self.provider,
                model=self.model
            ).dec()

            status = "error" if exc_type else "success"

            llm_requests_total.labels(
                provider=self.provider,
                model=self.model,
                task=self.task,
                status=status
            ).inc()

            llm_request_duration_seconds.labels(
                provider=self.provider,
                model=self.model,
                task=self.task
            ).observe(duration)

            if exc_type:
                error_type = exc_type.__name__ if exc_type else "unknown"
                llm_errors_total.labels(
                    provider=self.provider,
                    model=self.model,
                    error_type=error_type
                ).inc()

    return LLMRequestTracker(provider, model, task)


def record_llm_usage(
    provider: str,
    model: str,
    task: str,
    prompt_tokens: int,
    completion_tokens: int,
    cost: Optional[float] = None
):
    """Record LLM usage metrics."""
    llm_tokens_used.labels(
        provider=provider,
        model=model,
        task=task,
        type="prompt"
    ).inc(prompt_tokens)

    llm_tokens_used.labels(
        provider=provider,
        model=model,
        task=task,
        type="completion"
    ).inc(completion_tokens)

    if cost is not None:
        llm_cost.labels(
            provider=provider,
            model=model,
            task=task
        ).inc(cost)


def record_security_event(
    event_type: str,
    severity: str = "warning",
    blocked: bool = True
):
    """Record security event."""
    security_events_total.labels(
        event_type=event_type,
        severity=severity,
        blocked=str(blocked)
    ).inc()


def record_prompt_injection(pattern: str, blocked: bool = True):
    """Record prompt injection attempt."""
    prompt_injections_detected.labels(
        pattern=pattern,
        blocked=str(blocked)
    ).inc()

    record_security_event(
        event_type="prompt_injection",
        severity="high" if blocked else "critical",
        blocked=blocked
    )


def record_ssrf_attempt(reason: str):
    """Record SSRF attempt."""
    ssrf_attempts_blocked.labels(reason=reason).inc()
    record_security_event(
        event_type="ssrf_attempt",
        severity="high",
        blocked=True
    )


# ============================================================================
# Metrics Endpoint
# ============================================================================

def metrics_endpoint() -> Response:
    """Generate Prometheus metrics endpoint."""
    return Response(
        content=generate_latest(REGISTRY),
        media_type=CONTENT_TYPE_LATEST
    )


# ============================================================================
# System Info Collection
# ============================================================================

def update_system_info():
    """Update system information metrics."""
    import platform
    import sys

    system_info.info({
        'python_version': sys.version,
        'platform': platform.platform(),
        'processor': platform.processor(),
    })


def update_gpu_metrics():
    """Update GPU metrics if available."""
    try:
        import pynvml

        pynvml.nvmlInit()
        device_count = pynvml.nvmlDeviceGetCount()

        for i in range(device_count):
            handle = pynvml.nvmlDeviceGetHandleByIndex(i)

            # Memory
            mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
            gpu_memory_used_bytes.labels(device=str(i)).set(mem_info.used)

            # Utilization
            util = pynvml.nvmlDeviceGetUtilizationRates(handle)
            gpu_utilization_percent.labels(device=str(i)).set(util.gpu)

        pynvml.nvmlShutdown()

    except ImportError:
        logger.debug("pynvml not available, skipping GPU metrics")
    except Exception as e:
        logger.error(f"Error collecting GPU metrics: {e}")


# Initialize system info
update_system_info()
