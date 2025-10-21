#!/bin/bash

# Lab-Verse LocalAI Priority Setup Script
# Optimized for cost savings and time efficiency with LocalAI as primary provider

set -e

echo "🚀 Lab-Verse LocalAI Priority Setup - Cost & Time Optimized"
echo "========================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# Check system requirements
check_system() {
    print_info "Checking system requirements..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker not found. Please install Docker first."
        exit 1
    fi
    
    # Check available memory
    total_mem=$(free -m | awk 'NR==2{printf "%.0f", $2}')
    if [ "$total_mem" -lt 4096 ]; then
        print_warning "Less than 4GB RAM detected. LocalAI may run slowly."
    fi
    
    # Check disk space
    available_disk=$(df -h . | awk 'NR==2{print $4}' | sed 's/G//')
    if [ "$available_disk" -lt 10 ]; then
        print_warning "Less than 10GB disk space available. Models may not fit."
    fi
    
    print_status "System check completed"
}

# Setup LocalAI with optimized models
setup_localai() {
    print_info "Setting up LocalAI with cost-optimized models..."
    
    # Create models directory
    mkdir -p localai/models
    mkdir -p localai/config
    
    # Start LocalAI AIO (All-in-One) for fastest setup
    print_info "Starting LocalAI AIO with pre-configured models..."
    docker run -d --name lab-verse-localai \
        -p 8080:8080 \
        -v $(pwd)/localai/models:/models \
        -e DEBUG=true \
        -e THREADS=$(nproc) \
        localai/localai:latest-aio-cpu
    
    # Wait for LocalAI to start
    print_info "Waiting for LocalAI to initialize (this may take 2-3 minutes)..."
    timeout=300
    while ! curl -s http://localhost:8080/v1/models > /dev/null 2>&1; do
        sleep 10
        timeout=$((timeout - 10))
        if [ $timeout -le 0 ]; then
            print_error "LocalAI failed to start within 5 minutes"
            docker logs lab-verse-localai
            exit 1
        fi
        echo -n "."
    done
    echo ""
    
    print_status "LocalAI started successfully"
    
    # List available models
    print_info "Available LocalAI models:"
    curl -s http://localhost:8080/v1/models | jq -r '.data[].id' || echo "Model list not available yet"
}

# Setup n8n with LocalAI priority configuration
setup_n8n() {
    print_info "Setting up n8n with LocalAI priority..."
    
    # Create n8n directories
    mkdir -p n8n/workflows
    mkdir -p n8n/credentials
    
    # Start n8n with LocalAI-first configuration
    docker run -d --name lab-verse-n8n \
        -p 5678:5678 \
        -v $(pwd)/n8n:/home/node/.n8n \
        -e N8N_BASIC_AUTH_ACTIVE=true \
        -e N8N_BASIC_AUTH_USER=admin \
        -e N8N_BASIC_AUTH_PASSWORD=localai123 \
        -e USE_LOCAL=true \
        -e LOCALAI_BASE_URL=http://host.docker.internal:8080 \
        -e N8N_LOG_LEVEL=debug \
        n8nio/n8n:latest
    
    # Wait for n8n to start
    print_info "Waiting for n8n to start..."
    timeout=120
    while ! curl -s http://localhost:5678/healthz > /dev/null 2>&1; do
        sleep 5
        timeout=$((timeout - 5))
        if [ $timeout -le 0 ]; then
            print_error "n8n failed to start within 2 minutes"
            docker logs lab-verse-n8n
            exit 1
        fi
    done
    
    print_status "n8n started successfully"
}

# Test the complete integration
test_integration() {
    print_info "Testing LocalAI + n8n integration..."
    
    # Test LocalAI directly
    print_info "Testing LocalAI API..."
    localai_response=$(curl -s -X POST http://localhost:8080/v1/chat/completions \
        -H "Content-Type: application/json" \
        -d '{
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "Say hello from LocalAI"}],
            "temperature": 0.7,
            "max_tokens": 50
        }')
    
    if echo "$localai_response" | grep -q "choices"; then
        print_status "LocalAI API working"
        echo "LocalAI Response: $(echo $localai_response | jq -r '.choices[0].message.content')"
    else
        print_warning "LocalAI API test failed or still initializing"
        echo "Response: $localai_response"
    fi
    
    # Test n8n webhook (after workflow import)
    print_info "Testing n8n AI orchestration webhook..."
    print_warning "Please import the workflow first: n8n/workflows/lab-verse-ai-orchestration-complete.json"
    
    # Provide test command
    echo ""
    print_info "Once workflow is imported, test with:"
    echo "curl -X POST http://localhost:5678/webhook/ai-orchestration \\"
    echo "  -H 'Content-Type: application/json' \\"
    echo "  -d '{\"prompt\": \"Test LocalAI priority routing\"}'"
}

# Generate cost analysis
generate_cost_analysis() {
    print_info "Generating cost analysis for LocalAI vs Cloud providers..."
    
    cat > cost_analysis.md << 'EOF'
# Lab-Verse AI Cost Analysis - LocalAI vs Cloud Providers

## Cost Comparison (per 1M tokens)

| Provider | Model | Cost per 1M tokens | Privacy | Speed | Notes |
|----------|-------|-------------------|---------|-------|---------|
| **LocalAI** | phi-3 | $0.00 | High | Fast | Local processing, no API costs |
| **LocalAI** | llama-3.2-1b | $0.00 | High | Very Fast | Optimized for speed |
| **LocalAI** | mistral-7b | $0.00 | High | Fast | Good general purpose |
| Hugging Face | mistral-7b-instruct | $0.20 | Medium | Medium | Low-cost cloud option |
| OpenRouter | gpt-4o | $5.00 | Low | Medium | Premium but expensive |
| OpenRouter | gemini-pro | $1.50 | Low | Fast | Good balance |
| OpenRouter | llama-3-70b | $0.40 | Low | Slow | Large model, higher cost |

## Monthly Cost Projections

### Scenario: 100,000 requests/month (avg 500 tokens each = 50M tokens)

- **LocalAI Only**: $0/month + electricity (~$5-10/month)
- **Mixed (80% LocalAI, 20% Cloud)**: $10-50/month
- **Cloud Only**: $200-2500/month depending on models

### ROI Analysis
- **LocalAI Setup Cost**: One-time hardware + electricity
- **Break-even Point**: 1-2 months vs cloud-only approach
- **Annual Savings**: $2,400-30,000 depending on usage

## Performance Benefits
- **No Rate Limits**: Process unlimited requests
- **Low Latency**: No network overhead for local models
- **High Availability**: No dependency on external APIs
- **Data Privacy**: Sensitive data never leaves your infrastructure
EOF
    
    print_status "Cost analysis generated: cost_analysis.md"
}

# Main setup function
main() {
    echo "🎯 Lab-Verse LocalAI Priority Setup - Maximizing Cost & Time Savings"
    echo "==================================================================="
    
    check_system
    setup_localai
    setup_n8n
    test_integration
    generate_cost_analysis
    
    echo ""
    print_status "🎉 LocalAI Priority Setup Complete!"
    echo ""
    print_info "Access Points:"
    print_info "  🤖 LocalAI: http://localhost:8080"
    print_info "  🔄 n8n: http://localhost:5678 (admin/localai123)"
    echo ""
    print_info "Next Steps:"
    print_info "  1. Import workflow: n8n/workflows/lab-verse-ai-orchestration-complete.json"
    print_info "  2. Configure API credentials (optional for fallbacks)"
    print_info "  3. Test AI orchestration endpoint"
    print_info "  4. Monitor costs and performance"
    echo ""
    print_status "💰 Expected monthly savings: 90-95% vs cloud-only approach"
}

# Run main function
main "$@"