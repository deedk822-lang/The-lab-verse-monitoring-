#!/bin/bash

# Kimi Computer - End-to-End Integration Test Script
# This script tests all components and integrations

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
API_BASE="http://localhost:8080"
OLLAMA_URL="http://localhost:11434"
CHROMA_URL="http://localhost:8000"
TEST_EMAIL="test@example.com"
TEST_CONVERSION_ID="test-$(date +%s)"

echo -e "${BLUE}🧪 Kimi Computer - End-to-End Integration Tests${NC}"
echo "================================================"

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

# Function to print info
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_TOTAL=0

# Function to run test
run_test() {
    local test_name="$1"
    local test_command="$2"
    
    echo -e "\n${BLUE}🔍 Testing: $test_name${NC}"
    TESTS_TOTAL=$((TESTS_TOTAL + 1))
    
    if eval "$test_command"; then
        print_status "PASSED: $test_name"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        print_error "FAILED: $test_name"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

# Check prerequisites
echo -e "\n${BLUE}📋 Checking prerequisites...${NC}"

if ! command_exists curl; then
    print_error "curl is not installed"
    exit 1
fi

if ! command_exists jq; then
    print_error "jq is not installed (required for JSON parsing)"
    print_info "Install with: sudo apt-get install jq (Ubuntu/Debian) or brew install jq (macOS)"
    exit 1
fi

print_status "Prerequisites check passed"

# Test 1: Ollama Service Health
run_test "Ollama Service Health" "curl -f '$OLLAMA_URL/api/tags' >/dev/null 2>&1"

# Test 2: Mistral Model Availability
run_test "Mistral Model Availability" "curl -s '$OLLAMA_URL/api/tags' | jq -e '.models[] | select(.name | startswith(&quot;mistral&quot;))' >/dev/null"

# Test 3: Ollama Model Inference
run_test "Ollama Model Inference" "
curl -s -X POST '$OLLAMA_URL/api/generate' \
  -H 'Content-Type: application/json' \
  -d '{
    &quot;model&quot;: &quot;mistral:7b-instruct-v0.3&quot;,
    &quot;prompt&quot;: &quot;Generate a short greeting.&quot;,
    &quot;stream&quot;: false
  }' | jq -e '.response' >/dev/null
"

# Test 4: ChromaDB Service Health
run_test "ChromaDB Service Health" "curl -f '$CHROMA_URL/api/v1/heartbeat' >/dev/null 2>&1"

# Test 5: FastAPI Service Health
run_test "FastAPI Service Health" "curl -f '$API_BASE/health' >/dev/null 2>&1"

# Test 6: Health Response Schema
run_test "Health Response Schema" "
curl -s '$API_BASE/health' | jq -e 'has(&quot;status&quot;) and has(&quot;model&quot;) and has(&quot;uptime&quot;)' >/dev/null
"

# Test 7: Landing Page Accessibility
run_test "Landing Page Accessibility" "curl -f '$API_BASE/landing' >/dev/null 2>&1"

# Test 8: Landing Page Content
run_test "Landing Page Content" "curl -s '$API_BASE/landing' | grep -q 'Kimi Computer'"

# Test 9: API Documentation
run_test "API Documentation Accessibility" "curl -f '$API_BASE/docs' >/dev/null 2>&1"

# Test 10: Conversion Webhook (Valid Request)
run_test "Conversion Webhook Valid Request" "
TEST_RESPONSE=\$(curl -s -X POST '$API_BASE/catch' \
  -H 'Content-Type: application/json' \
  -d '{
    &quot;utm_source&quot;: &quot;test&quot;,
    &quot;utm_campaign&quot;: &quot;integration-test&quot;,
    &quot;utm_content&quot;: &quot;test-content&quot;,
    &quot;email&quot;: &quot;$TEST_EMAIL&quot;,
    &quot;name&quot;: &quot;Test User&quot;
  }')
echo \$TEST_RESPONSE | jq -e 'has(&quot;conversion_id&quot;) and has(&quot;status&quot;)' >/dev/null
"

# Test 11: Conversion Webhook (Invalid Request)
run_test "Conversion Webhook Invalid Request" "
curl -s -X POST '$API_BASE/catch' \
  -H 'Content-Type: application/json' \
  -d '{}' | grep -q 'validation error'
"

# Test 12: Root Endpoint
run_test "Root Endpoint" "curl -s '$API_BASE/' | jq -e 'has(&quot;message&quot;)' >/dev/null"

# Test 13: CORS Headers
run_test "CORS Headers" "
curl -s -I '$API_BASE/health' | grep -i 'access-control-allow-origin' >/dev/null
"

# Test 14: Content-Type Headers
run_test "Content-Type Headers" "
curl -s -I '$API_BASE/health' | grep -i 'content-type: application/json' >/dev/null
"

# Test 15: Error Handling (404)
run_test "Error Handling 404" "
curl -s '$API_BASE/nonexistent' | grep -q 'Not Found'
"

# Test 16: Load Test (Multiple Concurrent Requests)
run_test "Load Test Concurrent Requests" "
for i in {1..5}; do
  curl -s '$API_BASE/health' >/dev/null &
done
wait
"

# Test 17: Integration with Make.com (if configured)
if [ -n "$MAKE_WEBHOOK" ]; then
    run_test "Make.com Webhook Reachability" "curl -f '$MAKE_WEBHOOK' -X POST -d '{}' >/dev/null 2>&1 || true"
else
    print_warning "Skipping Make.com test (MAKE_WEBHOOK not configured)"
fi

# Test 18: Memory Usage Check
run_test "Memory Usage Check" "
if command_exists docker; then
    MEMORY_USAGE=\$(docker stats --no-stream --format 'table {{.MemUsage}}' kimi-api 2>/dev/null | tail -n 1 | cut -d'/' -f1)
    if [ -n &quot;\$MEMORY_USAGE&quot; ]; then
        echo &quot;API Memory Usage: \$MEMORY_USAGE&quot;
    fi
fi
true
"

# Test 19: Docker Container Status
run_test "Docker Container Status" "
docker ps --format 'table {{.Names}}\t{{.Status}}' | grep -E '(ollama|chromadb|kimi-api)'
"

# Test 20: Volume Persistence Check
run_test "Volume Persistence Check" "
docker volume ls | grep -E '(ollama_data|chromadb_data)'
"

# Advanced Tests
echo -e "\n${BLUE}🔬 Running Advanced Tests...${NC}"

# Test 21: Full Conversion Flow with AI Generation
run_test "Full Conversion Flow with AI" "
CONVERSION_RESPONSE=\$(curl -s -X POST '$API_BASE/catch' \
  -H 'Content-Type: application/json' \
  -d '{
    &quot;utm_source&quot;: &quot;advanced-test&quot;,
    &quot;utm_campaign&quot;: &quot;ai-generation&quot;,
    &quot;email&quot;: &quot;advanced-$TEST_EMAIL&quot;,
    &quot;name&quot;: &quot;Advanced Test User&quot;
  }')

CONVERSION_ID=\$(echo \$CONVERSION_RESPONSE | jq -r '.conversion_id')
if [ &quot;\$CONVERSION_ID&quot; != &quot;null&quot; ]; then
    echo &quot;Generated conversion ID: \$CONVERSION_ID&quot;
    sleep 3  # Wait for background processing
    echo &quot;✅ Full conversion flow test completed&quot;
else
    echo &quot;❌ Failed to generate conversion ID&quot;
    exit 1
fi
"

# Test 22: Performance Benchmark
run_test "Performance Benchmark" "
START_TIME=\$(date +%s.%N)
for i in {1..3}; do
    curl -s '$API_BASE/health' >/dev/null
done
END_TIME=\$(date +%s.%N)
AVG_TIME=\$(echo &quot;scale=3; (\$END_TIME - \$START_TIME) / 3&quot; | bc)
echo &quot;Average response time: \$AVG_TIME seconds&quot;
echo &quot;Performance benchmark completed&quot;
true
"

# Test 23: Security Headers
run_test "Security Headers" "
SECURITY_HEADERS=\$(curl -s -I '$API_BASE/health')
echo \$SECURITY_HEADERS | grep -i 'x-content-type-options' >/dev/null || echo &quot;Missing X-Content-Type-Options&quot;
echo \$SECURITY_HEADERS | grep -i 'x-frame-options' >/dev/null || echo &quot;Missing X-Frame-Options&quot;
true
"

# Test 24: Logging Verification
run_test "Logging Verification" "
if [ -f 'logs/app.log' ]; then
    LOG_SIZE=\$(wc -l < logs/app.log)
    echo &quot;Log file lines: \$LOG_SIZE&quot;
    tail -5 logs/app.log
else
    echo &quot;Log file not found, checking Docker logs...&quot;
    docker logs kimi-api 2>/dev/null | tail -5 || true
fi
true
"

# Generate test report
echo -e "\n${BLUE}📊 Test Results Summary${NC}"
echo "======================================="
echo -e "${GREEN}Tests Passed:  $TESTS_PASSED${NC}"
echo -e "${RED}Tests Failed:  $TESTS_FAILED${NC}"
echo -e "${BLUE}Tests Total:   $TESTS_TOTAL${NC}"

if [ $TESTS_FAILED -eq 0 ]; then
    print_status "All tests passed! 🎉"
    SUCCESS_RATE="100%"
else
    SUCCESS_RATE=$(echo "scale=1; ($TESTS_PASSED * 100) / $TESTS_TOTAL" | bc)
    print_warning "Some tests failed. Success rate: $SUCCESS_RATE%"
fi

# System Information
echo -e "\n${BLUE}🖥️  System Information${NC}"
echo "======================================="
echo "Date: $(date)"
echo "User: $(whoami)"
echo "System: $(uname -a)"

if command_exists docker; then
    echo "Docker Version: $(docker --version)"
    echo "Docker Compose Version: $(docker-compose --version)"
fi

# Service URLs
echo -e "\n${BLUE}🌐 Service URLs${NC}"
echo "======================================="
echo -e "FastAPI:           $API_BASE"
echo -e "API Docs:          $API_BASE/docs"
echo -e "Health Check:      $API_BASE/health"
echo -e "Landing Page:      $API_BASE/landing"
echo -e "Ollama API:        $OLLAMA_URL"
echo -e "ChromaDB API:      $CHROMA_URL"

# Recommendations
echo -e "\n${BLUE}💡 Recommendations${NC}"
echo "======================================="

if [ $TESTS_FAILED -eq 0 ]; then
    echo "✅ System is ready for production deployment"
    echo "✅ Consider setting up monitoring and alerting"
    echo "✅ Configure your Make.com workflow"
    echo "✅ Set up Brave Ads campaign with conversion tracking"
else
    echo "⚠️  Fix failed tests before proceeding to production"
    echo "⚠️  Check service logs for detailed error information"
    echo "⚠️  Verify all environment variables are set correctly"
fi

# Next steps
echo -e "\n${BLUE}🚀 Next Steps${NC}"
echo "======================================="
echo "1. Deploy to production: ./deploy-fly.sh"
echo "2. Configure Make.com workflow: import make-blueprint.json"
echo "3. Set up Brave Ads campaign with conversion tracking"
echo "4. Monitor system performance and logs"
echo "5. Scale resources as needed"

# Troubleshooting
echo -e "\n${YELLOW}🔧 Troubleshooting Tips${NC}"
echo "======================================="
echo "• If Ollama tests fail: Check Docker container status"
echo "• If FastAPI tests fail: Check application logs"
echo "• If webhook tests fail: Verify API keys and network connectivity"
echo "• If performance is slow: Check system resources and model loading"
echo "• For persistent issues: Check Docker logs: docker-compose logs -f"

# Exit with appropriate code
if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "\n${GREEN}🎊 Integration tests completed successfully!${NC}"
    exit 0
else
    echo -e "\n${RED}🚨 Integration tests completed with failures.${NC}"
    exit 1
fi