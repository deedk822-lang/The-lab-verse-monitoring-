"""
Prometheus Metrics
"""

from __future__ import annotations

from prometheus_client import Counter, Histogram, Gauge

# HTTP Metrics
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status_code"],
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency",
    ["method", "path"],
)

# LLM Metrics
llm_calls_total = Counter(
    "llm_calls_total",
    "Total LLM API calls",
    ["model", "status"],
)

llm_call_duration_seconds = Histogram(
    "llm_call_duration_seconds",
    "LLM call latency",
    ["model"],
)

# Database Metrics
db_pool_size = Gauge(
    "db_pool_size",
    "Database connection pool size",
)

db_pool_checked_out = Gauge(
    "db_pool_checked_out",
    "Database connections checked out",
)


def initialize_metrics() -> None:
    """Initialize Prometheus metrics."""
    pass  # Metrics auto-register on import
