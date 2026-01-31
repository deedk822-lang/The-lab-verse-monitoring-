#!/usr/bin/env bash
set -euo pipefail

required=(vaal-dashboard vaal-logs vaal-stop vaal-restart vaal-status vaal-emergency-stop)

missing=0
for cmd in "${required[@]}"; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "MISSING: $cmd"
    missing=1
  else
    echo "OK: $cmd -> $(command -v "$cmd")"
  fi
done

exit $missing
