#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8000}"

# Minimal, best-effort payload.
# If your API expects different fields (e.g. model/provider/max_tokens), adjust below.
payload='{"prompt":"Say hello in one short sentence."}'

curl -sS -X POST "${BASE_URL}/api/llm/generate" \
  -H 'Content-Type: application/json' \
  -d "$payload" | cat
echo ""
