# FIX: Pin to 'bookworm' (Debian Stable) to avoid unstable package crashes
FROM python:3.12-slim-bookworm

WORKDIR /app

# Install minimal system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# Copy root requirements
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip

# Install Python dependencies (including test tools)
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application structure
COPY rainmaker_orchestrator/ ./rainmaker_orchestrator/
COPY database.py .
COPY api/ ./api/
COPY agents/ ./agents/

ENV PYTHONPATH=/app
CMD ["python", "rainmaker_orchestrator/main.py"]
