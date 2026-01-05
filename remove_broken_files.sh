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
)

# Find and remove files matching the patterns
for pattern in "${PATTERNS[@]}"; do
  find . -name "$pattern" -type f -print -delete
done

echo "✅ [FILE CLEANER] Out-of-scope files removed."
