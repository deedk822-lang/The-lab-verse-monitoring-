#!/bin/bash
# ============================================================================
# Vercel Ignored Build Step
# Controls when Vercel should skip deployment
# ============================================================================

set -e

echo "🔍 Checking if build should be skipped..."

# Get current branch
BRANCH="${VERCEL_GIT_COMMIT_REF:-unknown}"
echo "📍 Branch: $BRANCH"

# Get commit message
COMMIT_MSG="${VERCEL_GIT_COMMIT_MESSAGE:-}"
echo "💬 Commit: $COMMIT_MSG"

# Skip if branch is not main or production
if [[ "$BRANCH" != "main" && "$BRANCH" != "master" && "$BRANCH" != "production" ]]; then
    echo "⏭️  Skipping: Not on main/production branch"
    exit 0  # 0 = skip build
fi

# Skip if commit message contains [skip-vercel]
if [[ "$COMMIT_MSG" == *"[skip-vercel]"* ]] || [[ "$COMMIT_MSG" == *"[vercel-skip]"* ]]; then
    echo "⏭️  Skipping: Commit message contains skip flag"
    exit 0
fi

# Skip if only documentation files changed
if git diff HEAD^ HEAD --name-only | grep -qvE '\.(md|txt|yml|yaml|sh)$|^(docs|k8s|scripts|monitoring)/'; then
    echo "✅ Building: Code changes detected"
    exit 1  # 1 = proceed with build
else
    echo "⏭️  Skipping: Only non-code files changed"
    exit 0
fi
