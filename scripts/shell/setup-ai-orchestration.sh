#!/bin/bash

# Lab-Verse AI Orchestration Setup Script
# This script sets up the complete Lab-Verse environment with n8n, LocalAI, and Hugging Face

set -e

echo "🚀 Lab-Verse AI Orchestration Setup Starting..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    print_info "Checking prerequisites..."
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    print_status "Prerequisites check passed"
}

# Create directory structure
create_directories() {
    print_info "Creating directory structure..."
    
    mkdir -p n8n/{workflows,credentials}
    mkdir -p localai/{models,config}
    mkdir -p nginx/ssl
    mkdir -p monitoring
    mkdir -p grafana/{dashboards,datasources}
    mkdir -p postgres/init
    mkdir -p logs
    
    print_status "Directory structure created"
}

# Setup environment file
setup_environment() {
    print_info "Setting up environment configuration..."
    
    if [ ! -f .env ]; then
        cp .env.ai.example .env
        print_warning "Please edit .env file with your API keys and configuration"
        print_info "Required API keys:"
        print_info "  - OPENROUTER_API_KEY: Get from https://openrouter.ai/"
        print_info "  - HUGGINGFACE_API_KEY: Get from https://huggingface.co/settings/tokens"
    else
        print_status "Environment file already exists"
    fi
}

# Download LocalAI models
download_models() {
    print_info "Downloading LocalAI models..."
    
    if [ ! -f localai/models/phi-3-mini-4k-instruct.Q4_K_M.gguf ]; then
        print_info "Downloading Phi-3 model (this may take a while)..."
        cd localai/models
        wget -q --show-progress https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf/resolve/main/Phi-3-mini-4k-instruct-q4.gguf -O phi-3-mini-4k-instruct.Q4_K_M.gguf
        cd ../..
        print_status "Phi-3 model downloaded"
    else
        print_status "Models already exist"
    fi
}

# Create LocalAI configuration
create_localai_config() {
    print_info "Creating LocalAI configuration..."
    
    cat > localai/config/phi-3.yaml << EOF
name: phi-3
backend: llama
parameters:
  model: phi-3-mini-4k-instruct.Q4_K_M.gguf
  top_k: 80
  temperature: 0.7
  top_p: 0.8
  context_size: 2048
  threads: 4
template:
  chat: |
    <|system|>{{.SystemPrompt}}<|end|>
    <|user|>{{.Input}}<|end|>
    <|assistant|>
EOF
    
    print_status "LocalAI configuration created"
}

# Create monitoring configuration
create_monitoring_config() {
    print_info "Creating monitoring configuration..."
    
    cat > monitoring/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'n8n'
    static_configs:
      - targets: ['n8n:5678']
  
  - job_name: 'localai'
    static_configs:
      - targets: ['localai:8080']
  
  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres:5432']
EOF
    
    print_status "Monitoring configuration created"
}

# Start services
start_services() {
    print_info "Starting Lab-Verse services..."
    
    # Start core services first
    docker-compose -f docker-compose.ai.yml up -d postgres redis qdrant
    sleep 10
    
    # Start LocalAI
    docker-compose -f docker-compose.ai.yml up -d localai
    sleep 30
    
    # Start n8n and other services
    docker-compose -f docker-compose.ai.yml up -d
    
    print_status "All services started"
}

# Import n8n workflow
import_workflow() {
    print_info "Waiting for n8n to be ready..."
    
    # Wait for n8n to be ready
    timeout=300
    while ! curl -s http://localhost:5678/healthz > /dev/null 2>&1; do
        sleep 5
        timeout=$((timeout - 5))
        if [ $timeout -le 0 ]; then
            print_error "n8n did not start within 5 minutes"
            exit 1
        fi
    done
    
    print_status "n8n is ready"
    print_info "Please manually import the workflow from n8n/workflows/lab-verse-ai-orchestration.json"
}

# Main execution
main() {
    echo "🔬 Lab-Verse AI Orchestration with LocalAI and Hugging Face"
    echo "============================================================"
    
    check_prerequisites
    create_directories
    setup_environment
    create_localai_config
    create_monitoring_config
    download_models
    start_services
    import_workflow
    
    echo ""
    print_status "🎉 Lab-Verse AI Orchestration setup completed!"
    echo ""
    print_info "Access points:"
    print_info "  📊 n8n: http://localhost:5678"
    print_info "  🤖 LocalAI: http://localhost:8080"
    print_info "  📈 Grafana: http://localhost:3000"
    print_info "  🔍 Prometheus: http://localhost:9090"
    echo ""
    print_warning "Next steps:"
    print_info "  1. Edit .env file with your API keys"
    print_info "  2. Import the workflow from n8n/workflows/lab-verse-ai-orchestration.json"
    print_info "  3. Configure credentials in n8n"
    print_info "  4. Test the AI orchestration endpoint"
}

# Run main function
main "$@"