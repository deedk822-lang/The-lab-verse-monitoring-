#!/bin/bash
set -euo pipefail

# Color codes
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly NC='\033[0m'

# Config
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly ENV_FILE="$SCRIPT_DIR/../.env"

# Safe environment loading
load_environment() {
    if [[ ! -f "$ENV_FILE" ]]; then
        echo -e "${RED}❌ .env file not found${NC}"
        exit 1
    fi

    set -a
    source "$ENV_FILE"
    set +a

    for var in KAGGLE_USERNAME KAGGLE_API_KEY GF_ADMIN_PASSWORD; do
        if [[ -z "${!var:-}" ]]; then
            echo -e "${RED}❌ $var not set${NC}"
            exit 1
        fi
    done
}

test_kaggle_api() {
    echo "🧪 Testing Kaggle API..."
    local http_status
    http_status=$(curl -s -o /dev/null -w "%{http_code}" \
        --max-time 10 \
        -u "$KAGGLE_USERNAME:$KAGGLE_API_KEY" \
        "https://www.kaggle.com/api/v1/datasets/list?page=1&pageSize=1")

    if [[ "$http_status" == "200" ]]; then
        echo -e "${GREEN}✅ Kaggle API works${NC}"
        return 0
    else
        echo -e "${RED}❌ Kaggle API failed (HTTP $http_status)${NC}"
        return 1
    fi
}

wait_for_grafana() {
    echo "⏳ Waiting for Grafana..."
    for i in {1..30}; do
        local health
        health=$(curl -s --max-time 5 http://localhost:3000/api/health 2>/dev/null || echo "")

        if echo "$health" | grep -q '"database".*"ok"'; then
            echo -e "${GREEN}✅ Grafana healthy${NC}"
            return 0
        fi

        if [[ $i -eq 30 ]]; then
            echo -e "${RED}❌ Grafana timeout${NC}"
            return 1
        fi

        sleep 2
    done
}

test_datasource() {
    echo "🔍 Testing datasource..."
    local response
    response=$(curl -s --max-time 10 \
        -u "admin:$GF_ADMIN_PASSWORD" \
        http://localhost:3000/api/datasources/name/Kaggle)

    if echo "$response" | grep -q '"name":"Kaggle"'; then
        echo -e "${GREEN}✅ Datasource configured${NC}"
        return 0
    else
        echo -e "${RED}❌ Datasource not found${NC}"
        return 1
    fi
}

main() {
    echo "🚀 Starting tests..."

    load_environment
    test_kaggle_api || exit 1
    wait_for_grafana || exit 1
    test_datasource || exit 1

    echo -e "${GREEN}✨ All tests passed!${NC}"
}

main "$@"
