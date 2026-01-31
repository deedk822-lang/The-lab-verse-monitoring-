# Multi-stage build for production-grade security and size
FROM python:3.11-slim AS builder

WORKDIR /build
COPY pyproject.toml ./
RUN pip install --no-cache-dir .

FROM python:3.11-slim AS runtime

# S7: Non-root user for hardening
RUN groupadd -r -g 10001 appgroup && \
    useradd -r -u 10001 -g appgroup appuser

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application source
COPY --chown=appuser:appgroup src/ ./src/

# Set secure permissions
RUN chmod -R 750 /app && \
    mkdir -p /app/logs && \
    chown -R appuser:appgroup /app/logs

# Switch to non-root user
USER appuser

EXPOSE 8000

ENV PYTHONPATH=/app/src

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/healthz || exit 1

CMD ["uvicorn", "pr_fix_agent.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
