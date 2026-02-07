FROM nvidia/cuda:12.1.1-devel-ubuntu22.04

# Install system deps
RUN apt-get update && apt-get install -y \
    python3.10 python3.10-dev python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages
RUN pip3 install --upgrade pip
RUN pip3 install vllm>=0.4.0 fla-core>=0.4.0

# Expose port
EXPOSE 8000

# Run command
CMD ["vllm", "serve", "Qwen/Qwen-72B-Instruct", \
     "--port", "8000", \
     "--tensor-parallel-size", "4", \
     "--max-model-len", "32768", \
     "--trust-remote-code"]
