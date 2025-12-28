FROM python:3.11-slim

WORKDIR /app

# Install dependencies first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8080

# Set environment variables at runtime (tokens injected via compose)
ENV LENS_API_TOKEN=
ENV KIMI_API_KEY=

CMD ["python", "app.py"]
