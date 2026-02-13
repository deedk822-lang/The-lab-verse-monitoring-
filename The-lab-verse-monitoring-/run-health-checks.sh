#!/bin/bash
set -euo pipefail

echo "Running health checks..."
echo ""

echo "Testing Nginx health endpoint..."
curl http://localhost/health
echo ""
echo ""

echo "Testing API health endpoint..."
curl http://localhost/api/health
echo ""
echo ""

echo "Testing API market-intel endpoint..."
curl -X POST http://localhost/api/market-intel \
  -H "Content-Type: application/json" \
  -d '{"company_name": "Microsoft", "refresh_cache": false}'
echo ""
