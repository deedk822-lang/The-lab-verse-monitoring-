from prometheus_client import Counter, Histogram, Gauge, Info, generate_latest
from prometheus_client import CONTENT_TYPE_LATEST, CollectorRegistry, multiprocess
from prometheus_client import make_asgi_app
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import time
import os

# Create registry for multiprocess mode (if using gunicorn/uvicorn workers)
registry = CollectorRegistry()
if os.environ.get('PROMETHEUS_MULTIPROC_DIR'):
    multiprocess.MultiProcessCollector(registry)

# Application info
app_info = Info('fastapi_app', 'FastAPI application information', registry=registry)
app_info.info({
    'version': '1.0.0',
    'python_version': '3.11',
    'framework': 'fastapi'
})

# Request metrics
http_requests_total = Counter(
    'fastapi_http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status'],
    registry=registry
)

http_request_duration_seconds = Histogram(
    'fastapi_http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    registry=registry,
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0)
)

http_requests_in_progress = Gauge(
    'fastapi_http_requests_in_progress',
    'HTTP requests currently in progress',
    ['method', 'endpoint'],
    registry=registry
)

# Business metrics
llm_requests_total = Counter(
    'fastapi_llm_requests_total',
    'Total LLM requests',
    ['backend', 'model', 'status'],
    registry=registry
)

llm_request_duration_seconds = Histogram(
    'fastapi_llm_request_duration_seconds',
    'LLM request duration in seconds',
    ['backend', 'model'],
    registry=registry,
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0)
)

llm_tokens_total = Counter(
    'fastapi_llm_tokens_total',
    'Total tokens processed',
    ['backend', 'model', 'type'],  # type: input/output
    registry=registry
)

# Database metrics
db_connections_active = Gauge(
    'fastapi_db_connections_active',
    'Active database connections',
    registry=registry
)

db_queries_total = Counter(
    'fastapi_db_queries_total',
    'Total database queries',
    ['operation', 'table', 'status'],
    registry=registry
)

db_query_duration_seconds = Histogram(
    'fastapi_db_query_duration_seconds',
    'Database query duration in seconds',
    ['operation', 'table'],
    registry=registry,
    buckets=(0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0)
)

# Redis metrics
redis_operations_total = Counter(
    'fastapi_redis_operations_total',
    'Total Redis operations',
    ['operation', 'status'],
    registry=registry
)

redis_operation_duration_seconds = Histogram(
    'fastapi_redis_operation_duration_seconds',
    'Redis operation duration in seconds',
    ['operation'],
    registry=registry,
    buckets=(0.001, 0.005, 0.01, 0.05, 0.1, 0.5)
)

# Rate limiting metrics
rate_limit_exceeded_total = Counter(
    'fastapi_rate_limit_exceeded_total',
    'Total rate limit exceeded events',
    ['endpoint', 'client'],
    registry=registry
)

# Error metrics
errors_total = Counter(
    'fastapi_errors_total',
    'Total errors',
    ['type', 'endpoint'],
    registry=registry
)


class PrometheusMiddleware(BaseHTTPMiddleware):
    """Middleware to collect HTTP metrics"""

    async def dispatch(self, request: Request, call_next):
        # Skip metrics endpoint
        if request.url.path == "/metrics":
            return await call_next(request)

        method = request.method
        endpoint = request.url.path

        # Track in-progress requests
        http_requests_in_progress.labels(method=method, endpoint=endpoint).inc()

        # Time the request
        start_time = time.time()

        try:
            response = await call_next(request)
            status = response.status_code

            # Record metrics
            http_requests_total.labels(
                method=method,
                endpoint=endpoint,
                status=status
            ).inc()

            duration = time.time() - start_time
            http_request_duration_seconds.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)

            return response

        except Exception as e:
            # Record error
            errors_total.labels(
                type=type(e).__name__,
                endpoint=endpoint
            ).inc()
            raise

        finally:
            # Decrement in-progress
            http_requests_in_progress.labels(method=method, endpoint=endpoint).dec()


def setup_metrics(app: ASGIApp):
    """Setup metrics endpoint"""

    # Add middleware
    app.add_middleware(PrometheusMiddleware)

    # Mount metrics endpoint
    metrics_app = make_asgi_app(registry=registry)
    app.mount("/metrics", metrics_app)

    return app
