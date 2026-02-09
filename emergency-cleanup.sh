#!/usr/bin/env bash
set -euo pipefail

mkdir -p .github/workflows.disabled

DUPLICATES=(
  "ci-cd.yml"
  "ci.yml"
  "type-safe-ci.yml"
  "verify-secrets.yml"
  "pr-validation.yml"
  "performance.yml"
)

for workflow in "${DUPLICATES[@]}"; do
  if [[ -f ".github/workflows/${workflow}" ]]; then
    mv ".github/workflows/${workflow}" .github/workflows.disabled/
    echo "disabled: ${workflow}"
  fi
done

if [[ -f .github/workflows/kimi-enhancer.yaml && -f .github/workflows/kimi-enhancer.yml ]]; then
  mv .github/workflows/kimi-enhancer.yaml .github/workflows.disabled/
  echo "disabled duplicate: kimi-enhancer.yaml"
fi

# Keep LLM review manual-only to avoid duplicate PR-triggered runs.
if [[ -f .github/workflows/llm-code-review.yml ]]; then
  python - <<'PY'
from pathlib import Path
import re
p = Path('.github/workflows/llm-code-review.yml')
t = p.read_text()
t = re.sub(r"on:\n(?:  pull_request:[\\s\\S]*?\n)?  workflow_dispatch:\n", "on:\n  workflow_dispatch:\n", t, count=1)
p.write_text(t)
PY
  echo "updated: llm-code-review.yml -> workflow_dispatch only"
fi

find .github/workflows -maxdepth 1 -type f \( -name "*.yml" -o -name "*.yaml" \) | sort
