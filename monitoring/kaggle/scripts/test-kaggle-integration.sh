#!/bin/bash
# monitoring/kaggle/scripts/test-kaggle-integration.sh - FIXED VERSION

set -euo pipefail  # Exit on error, undefined variables, pipe failures

# Color codes for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly NC='\033[0m' # No Color

# Configuration
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly ENV_FILE="${SCRIPT_DIR}/../.env"
readonly MAX_RETRIES=30
readonly RETRY_DELAY=2

# FIX 1: Safe environment variable loading
load_environment() {
    if [[ ! -f "$ENV_FILE" ]]; then
        echo -e "${RED}❌ .env file not found at: $ENV_FILE${NC}"
        exit 1
    fi

    # Safe sourcing with validation
    set -a
    # shellcheck source=/dev/null
    source "$ENV_FILE"
    set +a

    # Validate required variables
    local required_vars=(
        "KAGGLE_USERNAME"
        "KAGGLE_API_KEY"
        "GF_ADMIN_PASSWORD"
    )

    for var in "${required_vars[@]}"; do
        if [[ -z "${!var:-}" ]]; then
            echo -e "${RED}❌ Required variable $var is not set${NC}"
            exit 1
        fi
    done
}

# FIX 2: Safe curl with timeout and proper quoting
test_kaggle_api() {
    echo "🧪 Testing Kaggle API connection..."

    local http_status
    http_status=$(curl -s -o /dev/null -w "%{http_code}" \
        --max-time 10 \
        --connect-timeout 5 \
        -u "$KAGGLE_USERNAME:$KAGGLE_API_KEY" \
        "https://www.kaggle.com/api/v1/datasets/list?page=1&pageSize=1")

    if [[ "$http_status" == "200" ]]; then
        echo -e "${GREEN}✅ Kaggle API authentication successful${NC}"
        return 0
    else
        echo -e "${RED}❌ Kaggle API authentication failed (HTTP $http_status)${NC}"
        return 1
    fi
}

# FIX 3: Robust Grafana health check with content validation
wait_for_grafana() {
    echo "⏳ Waiting for Grafana to start..."

    local retry_count=0
    while [[ $retry_count -lt $MAX_RETRIES ]]; do
        local health_response
        health_response=$(curl -s --max-time 5 http://localhost:3000/api/health 2>/dev/null || echo "")

        if echo "$health_response" | grep -q '"database".*"ok"'; then
            echo -e "${GREEN}✅ Grafana is healthy${NC}"
            return 0
        fi

        ((retry_count++))
        if [[ $retry_count -eq $MAX_RETRIES ]]; then
            echo -e "${RED}❌ Grafana failed to start after ${MAX_RETRIES} attempts${NC}"
            echo "Last response: $health_response"
            return 1
        fi

        sleep $RETRY_DELAY
    done
}

# FIX 4: Datasource validation with proper error handling
test_datasource() {
    echo "🔍 Testing Grafana datasource..."

    local datasource_response
    datasource_response=$(curl -s --max-time 10 \
        -u "admin:$GF_ADMIN_PASSWORD" \
        http://localhost:3000/api/datasources/name/Kaggle 2>/dev/null || echo "")

    if echo "$datasource_response" | grep -q '"name":"Kaggle"'; then
        echo -e "${GREEN}✅ Kaggle datasource configured correctly${NC}"
        return 0
    else
        echo -e "${RED}❌ Kaggle datasource not found${NC}"
        echo "Response: $datasource_response"
        return 1
    fi
}

# Main execution
main() {
    echo "🚀 Starting Kaggle integration tests..."
    echo ""

    # Step 1: Load and validate environment
    load_environment

    # Step 2: Test Kaggle API
    if ! test_kaggle_api; then
        exit 1
    fi
    echo ""

    # Step 3: Wait for Grafana
    if ! wait_for_grafana; then
        exit 1
    fi
    echo ""

    # Step 4: Test datasource
    if ! test_datasource; then
        exit 1
    fi
    echo ""

    echo -e "${GREEN}✨ All integration tests passed successfully!${NC}"
    exit 0
}

# Run main function
main "$@"
