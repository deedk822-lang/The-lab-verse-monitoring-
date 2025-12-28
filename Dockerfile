# Dockerfile - FIXED
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ✅ CRITICAL: Set PYTHONPATH before copying code
ENV PYTHONPATH=/app:$PYTHONPATH

# Copy all application code
COPY . .

# ✅ Validate critical imports at build time
RUN python -c "from rainmaker_orchestrator import RainmakerOrchestrator; print('✅ rainmaker_orchestrator imported successfully')" || \
    (echo "❌ CRITICAL: rainmaker_orchestrator.py not found" && exit 1)

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Run the API server
CMD ["uvicorn", "api.server:app", "--host", "0.0.0.0", "--port", "8080", "--log-level", "info"]
