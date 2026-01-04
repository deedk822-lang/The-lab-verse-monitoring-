#!/bin/bash
set -euo pipefail

echo "Running k6 load test..."
echo "Please ensure you have k6 installed: https://k6.io/docs/getting-started/installation/"
echo ""

k6 run tests/load_test.js
