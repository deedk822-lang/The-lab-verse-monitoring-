"""
Prometheus Metrics - Global Production Standard
Tracks LLM performance, API latency, and errors.
"""

from prometheus_client import Counter, Histogram

# LLM Metrics
llm_calls_total = Counter(
    "llm_calls_total",
    "Total number of LLM API calls",
    ["model", "status"]
)

llm_call_duration_seconds = Histogram(
    "llm_call_duration_seconds",
    "Latency of LLM API calls in seconds",
    ["model"],
    buckets=(1, 5, 10, 30, 60, 90, 120, 180)
)

# HTTP Metrics
http_requests_total = Counter(
    "http_requests_total",
    "Total number of HTTP requests",
    ["method", "path", "status_code"]
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "Latency of HTTP requests in seconds",
    ["method", "path"],
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0)
)

# Database Metrics
db_pool_size = Counter(
    "db_pool_size",
    "Current database connection pool size"
)

# Rate Limit Metrics
rate_limit_hits_total = Counter(
    "rate_limit_hits_total",
    "Total number of rate limit violations"
)
