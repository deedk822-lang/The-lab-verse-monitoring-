#!/bin/bash
set -e

echo "🔍 Testing Kaggle API Integration..."

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "${RED}❌ .env file not found${NC}"
    exit 1
fi

# Check environment variables
if [ -z "$KAGGLE_USERNAME" ] || [ -z "$KAGGLE_API_KEY" ]; then
    echo "${RED}❌ KAGGLE_USERNAME or KAGGLE_API_KEY not set${NC}"
    exit 1
fi

echo "✅ Environment variables loaded"

# Test Kaggle API directly
echo "🧪 Testing Kaggle API connection..."
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -u "$KAGGLE_USERNAME:$KAGGLE_API_KEY" https://www.kaggle.com/api/v1/datasets/list?page=1&pageSize=1)

if [ "$HTTP_STATUS" = "200" ]; then
    echo "${GREEN}✅ Kaggle API authentication successful${NC}"
else
    echo "${RED}❌ Kaggle API returned status: $HTTP_STATUS${NC}"
    echo "Common issues:"
    echo "  - 401: Invalid credentials"
    echo "  - 403: API access disabled"
    echo "  - 429: Rate limit exceeded"
    exit 1
fi

# Wait for Grafana to be ready
echo "⏳ Waiting for Grafana to start..."
for i in {1..30}; do
    if curl -s http://localhost:3000/api/health > /dev/null; then
        echo "${GREEN}✅ Grafana is running${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "${RED}❌ Grafana failed to start${NC}"
        exit 1
    fi
    sleep 2
done

# Check datasource health
echo "🔍 Testing Grafana datasource..."
DATASOURCE_TEST=$(curl -s -u "admin:$GF_ADMIN_PASSWORD" \
    http://localhost:3000/api/datasources/name/Kaggle)

if echo "$DATASOURCE_TEST" | grep -q "\"name\":\"Kaggle\""; then
    echo "${GREEN}✅ Kaggle datasource configured${NC}"
else
    echo "${RED}❌ Kaggle datasource not found${NC}"
    exit 1
fi

echo ""
echo "${GREEN}🎉 All tests passed! Kaggle integration is working.${NC}"
echo ""
echo "Next steps:"
echo "1. Open Grafana: http://localhost:3000"
echo "2. Login with admin credentials"
echo "3. Navigate to the Kaggle API Integration dashboard"
