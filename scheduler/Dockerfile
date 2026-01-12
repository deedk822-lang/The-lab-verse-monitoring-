FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl && rm -rf /var/lib/apt/lists/*

COPY requirements-scheduler.txt .
RUN pip install --no-cache-dir -r requirements-scheduler.txt

COPY scheduler.py .

RUN useradd -m -u 1000 scheduler && chown -R scheduler:scheduler /app
USER scheduler

HEALTHCHECK --interval=60s --timeout=10s --start-period=10s --retries=3 \
  CMD python -c "import sys; sys.exit(0)"

CMD ["python", "scheduler.py"]
