#!/bin/bash
set -e

echo "🔀 CONSOLIDATING EMPIRE BRANCHES..."

# 1. ADD ALL NEW FILES
# This stages the Titans, the Bridge, the RAG engine, and the CFO.
git add vaal-ai-empire/src/
git add vaal-ai-empire/scripts/

# 2. COMMIT THE CONSOLIDATION
# We use a distinct message so you can track when the "Real Logic" landed.
git commit -m "feat(core): merge Titan, Glean, and RAG engines into production" || echo "Nothing to commit (already clean)"

echo "✅ CODEBASE SYNCED. Ready to update CI Pipeline."
