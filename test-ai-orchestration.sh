#!/bin/bash

# Lab-Verse AI Orchestration Test Script
# Tests all providers and fallback mechanisms

set -e

echo "🧪 Testing Lab-Verse AI Orchestration System..."

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

BASE_URL="http://localhost:5678/webhook/ai-orchestration"

print_test() {
    echo -e "${YELLOW}🧪 Testing: $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Test basic functionality
test_basic() {
    print_test "Basic AI request"
    
    response=$(curl -s -X POST $BASE_URL \
        -H "Content-Type: application/json" \
        -d '{"prompt": "Say hello in 5 words"}')
    
    if echo "$response" | grep -q "response"; then
        print_success "Basic request successful"
        echo "Response: $(echo $response | jq -r '.response')"
    else
        print_error "Basic request failed"
        echo "Response: $response"
        return 1
    fi
}

# Test local preference
test_local_preference() {
    print_test "Local AI preference"
    
    response=$(curl -s -X POST $BASE_URL \
        -H "Content-Type: application/json" \
        -d '{"prompt": "Generate a haiku", "prefer_local": true}')
    
    if echo "$response" | grep -q "localai"; then
        print_success "Local preference working"
    else
        print_error "Local preference not working"
        return 1
    fi
}

# Test provider routing
test_provider_routing() {
    print_test "Provider routing"
    
    # Test multiple requests to see different providers
    for i in {1..3}; do
        response=$(curl -s -X POST $BASE_URL \
            -H "Content-Type: application/json" \
            -d "{\"prompt\": \"Test request $i\"}")
        
        provider=$(echo $response | jq -r '.provider')
        model=$(echo $response | jq -r '.model')
        echo "Request $i: Provider=$provider, Model=$model"
    done
    
    print_success "Provider routing test completed"
}

# Test error handling
test_error_handling() {
    print_test "Error handling and fallback"
    
    # Test with invalid request
    response=$(curl -s -X POST $BASE_URL \
        -H "Content-Type: application/json" \
        -d '{"invalid": "request"}')
    
    if echo "$response" | grep -q "error"; then
        print_success "Error handling working"
    else
        print_error "Error handling not working properly"
    fi
}

# Test performance
test_performance() {
    print_test "Performance benchmarking"
    
    start_time=$(date +%s%N)
    
    for i in {1..5}; do
        curl -s -X POST $BASE_URL \
            -H "Content-Type: application/json" \
            -d '{"prompt": "Quick test"}' > /dev/null
    done
    
    end_time=$(date +%s%N)
    duration=$(((end_time - start_time) / 1000000))
    avg_time=$((duration / 5))
    
    print_success "Average response time: ${avg_time}ms"
}

# Run all tests
main() {
    echo "🚀 Lab-Verse AI Orchestration Test Suite"
    echo "========================================"
    
    test_basic || exit 1
    sleep 2
    
    test_local_preference || echo "⚠️ Local preference test failed (may be expected)"
    sleep 2
    
    test_provider_routing
    sleep 2
    
    test_error_handling
    sleep 2
    
    test_performance
    
    echo ""
    print_success "🎉 All tests completed!"
    echo ""
    echo "📊 Check Grafana dashboard at http://localhost:3000"
    echo "📈 Check Prometheus metrics at http://localhost:9090"
}

main "$@"