# ============================================================================
# VAAL AI Empire - Multi-stage Production Dockerfile
# ============================================================================

# ----------------------------------------------------------------------------
# Builder Stage - Compile dependencies and prepare environment
# ----------------------------------------------------------------------------
FROM nvidia/cuda:12.1.0-cudnn8-devel-ubuntu22.04 AS builder

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.10 \
    python3.10-dev \
    python3-pip \
    build-essential \
    git \
    curl \
    wget \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install build tools
RUN python3.10 -m pip install --upgrade pip setuptools wheel

# Create working directory
WORKDIR /build

# Copy requirements first for better caching
COPY requirements.txt requirements-dev.txt ./

# Install Python dependencies
RUN pip install --user --no-warn-script-location \
    -r requirements.txt && \
    pip install --user --no-warn-script-location \
    gunicorn uvicorn[standard]

# ----------------------------------------------------------------------------
# Runtime Stage - Minimal production image
# ----------------------------------------------------------------------------
FROM nvidia/cuda:12.1.0-cudnn8-runtime-ubuntu22.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH=/root/.local/bin:$PATH \
    NVIDIA_VISIBLE_DEVICES=all \
    NVIDIA_DRIVER_CAPABILITIES=compute,utility

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.10 \
    python3.10-distutils \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd -m -u 1000 -s /bin/bash vaaluser && \
    mkdir -p /app /models /cache /logs && \
    chown -R vaaluser:vaaluser /app /models /cache /logs

# Copy Python packages from builder
COPY --from=builder --chown=vaaluser:vaaluser /root/.local /root/.local

# Set working directory
WORKDIR /app

# Copy application code
COPY --chown=vaaluser:vaaluser . .

# Create necessary directories
RUN mkdir -p \
    /app/vaal_ai_empire/api \
    /app/agent/tools \
    /app/agent/nodes \
    /app/logs \
    /app/uploads

# Set permissions
RUN chmod +x scripts/*.sh 2>/dev/null || true

# Switch to non-root user
USER vaaluser

# Expose ports
EXPOSE 8000 9090

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command
CMD ["gunicorn", "app.main:app", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "4", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--timeout", "300", \
     "--graceful-timeout", "120", \
     "--keep-alive", "5", \
     "--log-level", "info", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]

# Alternative CMD for development
# CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Labels
LABEL maintainer="VAAL AI Empire Team" \
      version="2.0.0" \
      description="Multi-provider LLM system with security hardening" \
      org.opencontainers.image.source="https://github.com/deedk822-lang/The-lab-verse-monitoring-"
