#!/bin/bash
set -e

echo "🔍 [FILE CLEANER] Identifying and removing out-of-scope files..."

# Define patterns for out-of-scope files
PATTERNS=(
  "*asana*"
  "*g20*"
  "*rankyak*"
  "*mock*"
  "*simulation*"
  "test_content_factory_perf.py"
  "Untitled File 2025-12-02 02_34_59.py"
  "performance_test.py"
)

# Find and remove files matching the patterns
for pattern in "${PATTERNS[@]}"; do
  find . -name "$pattern" -type f -print -delete
done

echo "✅ [FILE CLEANER] Out-of-scope files removed."
