#!/bin/bash
# scripts/performance_benchmarks.sh
# Runs all performance benchmarks

set -euo pipefail

SCRIPT_DIR=$(dirname "$(realpath "$0")")
PROJECT_ROOT=$(realpath "$SCRIPT_DIR/..")

cd "$PROJECT_ROOT"

# Install Node.js dependencies if not already installed
if [ ! -d "node_modules" ]; then
  echo "Node.js dependencies not found, installing..."
  npm install
fi

# Run the performance monitor
node src/backend/performance/monitor.js   --config src/backend/performance/config.js   --base-url "${BASE_URL:-http://localhost:3000}"   --redis "${REDIS_URL:-}"   --duration "${BENCH_DURATION_SEC:-20}"   --warmup "${BENCH_WARMUP_SEC:-3}"   --timeout "${BENCH_TIMEOUT_SEC:-30}"   --min-concurrency "${BENCH_MIN_CONCURRENCY:-50}"   --max-concurrency "${BENCH_MAX_CONCURRENCY:-500}"   --step "${BENCH_CONCURRENCY_STEP:-50}"   --conn-reuse "${BENCH_CONN_REUSE:-true}"

echo "Performance benchmarks completed."
