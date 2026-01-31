#!/usr/bin/env bash
set -euo pipefail

# Helper runner for Kimi CLI.
# Usage:
#   export KIMI_API_KEY=sk-moonshot-...
#   ./kimi/run-with-kimi.sh

if [[ -z "${KIMI_API_KEY:-}" ]]; then
  echo "KIMI_API_KEY is not set."
  echo "Example: export KIMI_API_KEY=sk-moonshot-your-key"
  exit 1
fi

# Some parts of the stack use KIMIAPIKEY.
export KIMIAPIKEY="${KIMIAPIKEY:-$KIMI_API_KEY}"

pip install -q kimi-cli

kimi run --config kimi/kimi-cli-config.yml
