# Stage 1: Builder
FROM python:3.9-slim as builder

# Install poetry
RUN pip install poetry

WORKDIR /app

# Copy only files necessary for dependency installation
COPY pyproject.toml poetry.lock ./

# Ensure Poetry creates the virtualenv inside the project (so /app/.venv exists)
ENV POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1

# Install dependencies (Poetry 1.2+ replaces --no-dev with dependency groups)
RUN poetry install --no-root --only main

# Stage 2: Production
FROM nvidia/cuda:12.1-devel-ubuntu22.04

# Singapore region optimization
ENV TZ=Asia/Singapore
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# System updates
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy installed dependencies from builder stage
COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Copy application code
COPY app/ ./app/

# Singapore region environment
ENV ALIBABA_CLOUD_REGION_ID=ap-southeast-1

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
