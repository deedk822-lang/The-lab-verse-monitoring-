# Multi-stage build for Rainmaker Orchestrator
# Stage 1: Builder
FROM python:3.12-slim-bookworm AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install to a virtual environment
COPY requirements.txt .
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.12-slim-bookworm

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY . .

# Create non-root user for security
RUN useradd -m -u 1000 -s /bin/bash appuser && \
    chown -R appuser:appuser /app && \
    mkdir /workspace && \
    chown -R appuser:appuser /workspace

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8080

# Add healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1

# Use environment variables for Gunicorn configuration
ENV GUNICORN_WORKERS=4
ENV GUNICORN_TIMEOUT=120
ENV GUNICORN_KEEPALIVE=5
ENV GUNICORN_MAX_REQUESTS=1000
ENV GUNICORN_MAX_REQUESTS_JITTER=100

# Run Gunicorn with production settings
CMD gunicorn \
    --bind 0.0.0.0:8080 \
    --workers ${GUNICORN_WORKERS} \
    --timeout ${GUNICORN_TIMEOUT} \
    --keep-alive ${GUNICORN_KEEPALIVE} \
    --max-requests ${GUNICORN_MAX_REQUESTS} \
    --max-requests-jitter ${GUNICORN_MAX_REQUESTS_JITTER} \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    --worker-class sync \
    --threads 2 \
    server:app
