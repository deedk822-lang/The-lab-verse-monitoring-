#!/bin/bash

# LocalAI Installation Script
# This script installs LocalAI and downloads recommended models

set -e

echo "🚀 Installing LocalAI..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is required but not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is required but not installed. Please install Docker Compose first."
    exit 1
fi

echo "✅ Docker and Docker Compose are available"

# Create LocalAI directory
LOCALAI_DIR="./localai"
mkdir -p "$LOCALAI_DIR"
cd "$LOCALAI_DIR"

# Download LocalAI binary
echo "📥 Downloading LocalAI binary..."
LOCALAI_VERSION="v1.0.0"
wget -O local-ai "https://github.com/go-skynet/LocalAI/releases/download/${LOCALAI_VERSION}/LocalAI_Linux_x86_64"
chmod +x local-ai

# Create models directory
mkdir -p models

# Download recommended models
echo "📥 Downloading recommended models..."

# Download a small language model for testing
echo "  - Downloading llama-3.2-1b-instruct..."
wget -O models/llama-3.2-1b-instruct.yaml "https://huggingface.co/microsoft/DialoGPT-medium/resolve/main/config.json"

# Create model configuration
cat > models/llama-3.2-1b-instruct.yaml << EOF
name: llama-3.2-1b-instruct
backend: llama
parameters:
  model: llama-3.2-1b-instruct
  context_size: 4096
  threads: 4
  f16: true
  debug: true
  stopwords:
    - "Human:"
    - "Assistant:"
  template: |
    {{ if .System }}<|start_header_id|>system<|end_header_id|>

    {{ .System }}<|eot_id|>{{ end }}{{ if .Prompt }}<|start_header_id|>user<|end_header_id|>

    {{ .Prompt }}<|eot_id|><|start_header_id|>assistant<|end_header_id|>

    {{ .Response }}<|eot_id|>{{ end }}
EOF

# Download Stable Diffusion model for image generation
echo "  - Downloading Stable Diffusion model..."
mkdir -p models/stability-ai
wget -O models/stability-ai/stable-diffusion.yaml "https://raw.githubusercontent.com/go-skynet/LocalAI/master/examples/configs/stable-diffusion.yaml"

# Create startup script
cat > start-localai.sh << 'EOF'
#!/bin/bash
echo "🚀 Starting LocalAI..."
./local-ai run --models-path ./models --threads 4 --context-size 4096 --debug
EOF

chmod +x start-localai.sh

# Create Docker Compose file for LocalAI
cat > docker-compose.localai.yml << 'EOF'
version: '3.8'

services:
  localai:
    image: localai/localai:latest
    ports:
      - "8080:8080"
    environment:
      - MODELS_PATH=/models
      - THREADS=4
      - CONTEXT_SIZE=4096
      - DEBUG=true
    volumes:
      - ./models:/models
    restart: unless-stopped
    command: local-ai run --models-path /models --threads 4 --context-size 4096
EOF

echo "✅ LocalAI installation completed!"
echo ""
echo "To start LocalAI:"
echo "1. cd $LOCALAI_DIR"
echo "2. ./start-localai.sh"
echo ""
echo "Or with Docker:"
echo "1. cd $LOCALAI_DIR"
echo "2. docker-compose -f docker-compose.localai.yml up -d"
echo ""
echo "LocalAI will be available at http://localhost:8080"
echo "Update your .env file with: LOCALAI_URL=http://localhost:8080"