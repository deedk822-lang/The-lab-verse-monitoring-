#!/bin/bash

# Kimi Computer - Mistral Setup Script
# This script sets up Mistral-7B model for local inference

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
OLLAMA_HOST="${OLLAMA_HOST:-http://localhost:11434}"
MISTRAL_MODEL="mistral"
MISTRAL_TAG="7b-instruct-v0.3"
FULL_MODEL_NAME="${MISTRAL_MODEL}:${MISTRAL_TAG}"

echo -e "${BLUE}🚀 Kimi Computer - Mistral Setup${NC}"
echo "======================================="

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to print status
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

# Function to print warning
print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Function to print error
print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check prerequisites
echo -e "\n${BLUE}📋 Checking prerequisites...${NC}"

if ! command_exists docker; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command_exists curl; then
    print_error "curl is not installed. Please install curl first."
    exit 1
fi

print_status "Prerequisites check passed"

# Check if Ollama container is running
echo -e "\n${BLUE}🔍 Checking Ollama service...${NC}"

if docker ps | grep -q ollama; then
    print_status "Ollama container is running"
else
    print_warning "Ollama container is not running. Starting it..."
    
    # Start Ollama container
    docker run -d \
        --name ollama \
        --restart unless-stopped \
        -p 11434:11434 \
        -v ollama_data:/root/.ollama \
        ollama/ollama:latest
    
    print_status "Ollama container started"
    
    # Wait for Ollama to be ready
    echo "Waiting for Ollama to be ready..."
    for i in {1..30}; do
        if curl -f "$OLLAMA_HOST/api/tags" >/dev/null 2>&1; then
            print_status "Ollama is ready"
            break
        fi
        echo -n "."
        sleep 2
    done
fi

# Check if Mistral model is already downloaded
echo -e "\n${BLUE}🔍 Checking Mistral model...${NC}"

if curl -s "$OLLAMA_HOST/api/tags" | grep -q "$FULL_MODEL_NAME"; then
    print_status "Mistral $FULL_MODEL_NAME is already downloaded"
else
    echo "Downloading Mistral $FULL_MODEL_NAME..."
    
    # Download Mistral model
    docker exec ollama ollama pull "$FULL_MODEL_NAME"
    
    if [ $? -eq 0 ]; then
        print_status "Mistral $FULL_MODEL_NAME downloaded successfully"
    else
        print_error "Failed to download Mistral model"
        exit 1
    fi
fi

# Test model inference
echo -e "\n${BLUE}🧪 Testing model inference...${NC}"

TEST_PROMPT="Write a short tweet about AI automation (max 280 characters):"

echo "Sending test prompt: '$TEST_PROMPT'"

RESPONSE=$(curl -s -X POST "$OLLAMA_HOST/api/generate" \
    -H "Content-Type: application/json" \
    -d "{
        &quot;model&quot;: &quot;$FULL_MODEL_NAME&quot;,
        &quot;prompt&quot;: &quot;$TEST_PROMPT&quot;,
        &quot;stream&quot;: false,
        &quot;options&quot;: {
            &quot;temperature&quot;: 0.7,
            &quot;top_p&quot;: 0.9,
            &quot;max_tokens&quot;: 100
        }
    }")

if [ $? -eq 0 ]; then
    # Extract the response text
    GENERATED_TEXT=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('response', '').strip())")
    
    if [ -n "$GENERATED_TEXT" ]; then
        print_status "Model inference test passed"
        echo -e "${GREEN}Generated content:${NC} $GENERATED_TEXT"
    else
        print_error "Empty response from model"
        exit 1
    fi
else
    print_error "Model inference test failed"
    exit 1
fi

# Get model information
echo -e "\n${BLUE}📊 Model information...${NC}"

MODEL_INFO=$(curl -s "$OLLAMA_HOST/api/tags" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for model in data.get('models', []):
    if '$FULL_MODEL_NAME' in model.get('name', ''):
        print(f'Model: {model[&quot;name&quot;]}')
        print(f'Size: {model.get(&quot;size&quot;, &quot;unknown&quot;) / (1024**3):.2f} GB')
        print(f'Modified: {model.get(&quot;modified_at&quot;, &quot;unknown&quot;)}')
        break
")

echo "$MODEL_INFO"

# Performance benchmark
echo -e "\n${BLUE}⚡ Performance benchmark...${NC}"

echo "Running performance test (3 consecutive generations)..."

TOTAL_TIME=0
for i in {1..3}; do
    START_TIME=$(date +%s.%N)
    
    curl -s -X POST "$OLLAMA_HOST/api/generate" \
        -H "Content-Type: application/json" \
        -d "{
            &quot;model&quot;: &quot;$FULL_MODEL_NAME&quot;,
            &quot;prompt&quot;: &quot;Generate a short sentence.&quot;,
            &quot;stream&quot;: false
        }" >/dev/null
    
    END_TIME=$(date +%s.%N)
    DURATION=$(echo "$END_TIME - $START_TIME" | bc)
    TOTAL_TIME=$(echo "$TOTAL_TIME + $DURATION" | bc)
    
    echo "Test $i: ${DURATION}s"
done

AVG_TIME=$(echo "scale=2; $TOTAL_TIME / 3" | bc)
TOKENS_PER_SEC=$(echo "scale=0; 50 / $AVG_TIME" | bc)

print_status "Performance benchmark completed"
echo "Average generation time: ${AVG_TIME}s"
echo "Estimated tokens/sec: ${TOKENS_PER_SEC}"

# Memory usage check
echo -e "\n${BLUE}💾 Memory usage...${NC}"

if command_exists docker; then
    MEMORY_USAGE=$(docker stats ollama --no-stream --format "table {{.MemUsage}}")
    echo "Ollama container memory usage:"
    echo "$MEMORY_USAGE"
fi

# System information
echo -e "\n${BLUE}🖥️  System information...${NC}"

if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    if command_exists sysctl; then
        MEMORY_TOTAL=$(sysctl -n hw.memsize | awk '{print $1/1024^3 " GB"}')
        CPU_INFO=$(sysctl -n machdep.cpu.brand_string)
        echo "OS: macOS"
        echo "CPU: $CPU_INFO"
        echo "Total RAM: $MEMORY_TOTAL"
    fi
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    if command_exists free && command_exists lscpu; then
        MEMORY_TOTAL=$(free -h | awk '/^Mem:/ {print $2}')
        CPU_INFO=$(lscpu | grep 'Model name' | cut -d':' -f2- | xargs)
        echo "OS: Linux"
        echo "CPU: $CPU_INFO"
        echo "Total RAM: $MEMORY_TOTAL"
    fi
fi

# Final status
echo -e "\n${BLUE}🎉 Setup complete!${NC}"
echo "======================================="
print_status "Mistral $FULL_MODEL_NAME is ready for use"
print_status "API endpoint: $OLLAMA_HOST"
print_status "Model: $FULL_MODEL_NAME"

# Recommendations
echo -e "\n${YELLOW}💡 Recommendations:${NC}"
echo "• For better performance, ensure you have at least 16GB RAM"
echo "• Consider upgrading to Mixtral-8x7B for higher quality (requires 32GB+ RAM)"
echo "• Monitor GPU usage if available for faster inference"

# Next steps
echo -e "\n${BLUE}🚀 Next steps:${NC}"
echo "1. Start the Kimi Computer API: docker-compose up -d kimi-api"
echo "2. Check API health: curl http://localhost:8080/health"
echo "3. Test conversion endpoint: curl -X POST http://localhost:8080/catch -d '{&quot;utm_source&quot;:&quot;test&quot;}'"

echo -e "\n${GREEN}✨ Your Kimi Computer is ready!${NC}"