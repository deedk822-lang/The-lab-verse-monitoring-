FROM nvidia/cuda:12.1-devel-ubuntu22.04

# Singapore region optimization
ENV TZ=Asia/Singapore
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# System updates
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    git \
    curl \
    wget \
    vim \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt

# Copy application
COPY . /app/

# Install any dev dependencies for testing
RUN pip3 install pytest pytest-asyncio black flake8 mypy

# Singapore region environment
ENV ALIBABA_CLOUD_REGION_ID=ap-southeast-1

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
