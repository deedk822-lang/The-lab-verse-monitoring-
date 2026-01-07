# agents/frontend/Dockerfile
FROM python:3.12-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1

COPY ./agents/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY ./agents /app/agents

CMD ["uvicorn", "agents.frontend.web_worker:app", "--host", "0.0.0.0", "--port", "8080", "--loop", "uvloop", "--workers", "1"]
