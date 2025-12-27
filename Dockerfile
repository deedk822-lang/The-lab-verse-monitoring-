FROM python:3.9-slim
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ⭐ KEY FIX: Set global Python path
ENV PYTHONPATH=/app:$PYTHONPATH

# Copy code
COPY . .

# ⭐ Build-time verification (Simplified)
RUN python -c "import rainmaker_orchestrator; print('✅ Import successful in Docker build')" || \
    (echo "❌ Import failed - rainmaker_orchestrator.py not found" && exit 1)

CMD ["uvicorn", "api.server:app", "--host", "0.0.0.0", "--port", "8080", "--log-level", "info"]
