#!/bin/bash
set -e

echo "🔍 [VALIDATOR] Starting Deep Scan..."

# 1. Syntax Check (Python/JS)
# Prevents Kimi from generating hallucinated syntax
find . -name "*.py" -exec python3 -m py_compile {} \;
find . -name "*.js" -exec node --check {} \;

# 2. Dependency Vulnerability Check
if [ -f "package.json" ]; then
    npm audit --production --audit-level=high
fi

# 3. Secret Scanning (Local TruffleHog)
# Ensures Kimi didn't generate a fake API key that looks real
if command -v trufflehog &> /dev/null; then
    trufflehog filesystem . --no-verification --fail
fi

# 4. Semgrep SAST (The Custom Ruleset)
semgrep scan --config=.semgrep.yml --error

echo "✅ [VALIDATOR] All Gates Passed."
