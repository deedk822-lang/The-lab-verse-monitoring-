# Dockerfile - 修复版
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# ⭐ 关键修复：设置全局 Python 路径
ENV PYTHONPATH=/app:$PYTHONPATH

# Copy application code
COPY . .

# ⭐ 构建时验证导入（失败则构建失败）
RUN python -c "import sys; sys.path.insert(0, '/app'); from rainmaker_orchestrator import RainmakerOrchestrator; print('✅ Import successful')" || \
    (echo "❌ Import failed - rainmaker_orchestrator.py not found" && exit 1)

# Run the API server
CMD ["uvicorn", "api.server:app", "--host", "0.0.0.0", "--port", "8080", "--log-level", "info"]