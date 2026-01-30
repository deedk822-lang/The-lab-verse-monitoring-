# ============================================================================
# Stage 1: Builder
# ============================================================================
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast package installation
RUN pip install --no-cache-dir uv

# Copy dependency files
COPY pyproject.toml uv.lock* ./

# Install Python dependencies
RUN uv pip install --system --no-cache \
    --requirement pyproject.toml \
    --extra dev

# ============================================================================
# Stage 2: Runtime
# ============================================================================
FROM python:3.11-slim AS runtime

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# S7: Create non-root user (UID 10001)
RUN groupadd -r -g 10001 appgroup && \
    useradd -r -u 10001 -g appgroup -m -d /home/appuser -s /sbin/nologin appuser

# Create application directory
WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY --chown=appuser:appgroup src/ ./src/
COPY --chown=appuser:appgroup alembic.ini ./
COPY --chown=appuser:appgroup migrations/ ./migrations/

# S7: Set secure permissions (750 = rwxr-x---)
RUN chmod -R 750 /app && \
    chown -R appuser:appgroup /app

# Create directories for logs and temporary files
RUN mkdir -p /app/logs /tmp/prometheus && \
    chown -R appuser:appgroup /app/logs /tmp/prometheus && \
    chmod 750 /app/logs /tmp/prometheus

# S7: Switch to non-root user
USER appuser

# Set Python path
ENV PYTHONPATH=/app/src
ENV PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/healthz || exit 1

# Expose port
EXPOSE 8000

# S7: Label for read-only filesystem requirement
LABEL security.readonly="true" \
      security.user="appuser:10001" \
      security.seccomp="enabled" \
      version="0.1.0" \
      maintainer="team@example.com"

# Run application
# Use exec form to ensure proper signal handling
CMD ["uvicorn", "pr_fix_agent.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
