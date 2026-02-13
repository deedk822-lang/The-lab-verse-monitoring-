#!/usr/bin/env bash
set -euo pipefail

# The Lab Verse Monitoring Stack - Performance Benchmarks Runner
# Node.js 14+ required.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PERF_DIR="${ROOT_DIR}/src/backend/performance"
RESULTS_DIR="${RESULTS_DIR:-${ROOT_DIR}/results}"

export NODE_ENV="${NODE_ENV:-development}"
export BASE_URL="${BASE_URL:-http://localhost:3000}"
export LOG_LEVEL="${LOG_LEVEL:-info}"

# Optional: Redis for storing lightweight summaries
# export REDIS_URL="redis://localhost:6379"

# Tunables (override per environment)
export BENCH_DURATION_SEC="${BENCH_DURATION_SEC:-20}"
export BENCH_WARMUP_SEC="${BENCH_WARMUP_SEC:-3}"
export BENCH_TIMEOUT_SEC="${BENCH_TIMEOUT_SEC:-30}"
export BENCH_MIN_CONCURRENCY="${BENCH_MIN_CONCURRENCY:-50}"
export BENCH_MAX_CONCURRENCY="${BENCH_MAX_CONCURRENCY:-500}"
export BENCH_CONCURRENCY_STEP="${BENCH_CONCURRENCY_STEP:-50}"
export MAX_MEM_MB="${MAX_MEM_MB:-1024}"

echo "==> Results dir: ${RESULTS_DIR}"
mkdir -p "${RESULTS_DIR}"

echo "==> Installing perf tooling dependencies"
cd "${PERF_DIR}"

if [[ -f package-lock.json ]]; then
  npm ci
else
  npm install
fi

echo "==> Running benchmarks against BASE_URL=${BASE_URL}"
node "${PERF_DIR}/monitor.js" \
  --config "${PERF_DIR}/config.js" \
  --out "${RESULTS_DIR}" \
  --base-url "${BASE_URL}" \
  --redis "${REDIS_URL:-}"

echo "==> Running analysis (latest run)"
node "${PERF_DIR}/analyze.js" --results "${RESULTS_DIR}"

echo "==> Running recommendations (latest run)"
node "${PERF_DIR}/recommendations.js" --results "${RESULTS_DIR}" --config "${PERF_DIR}/config.js"

echo "==> Done. See results/ for summary.json, report.txt, and recommendations.txt."
