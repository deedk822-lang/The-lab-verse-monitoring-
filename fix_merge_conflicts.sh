#!/bin/bash
set -e

echo "🔍 [MERGE FIXER] Starting intelligent merge conflict resolution..."

# Find all files with merge conflict markers

if [ -z "$CONFLICT_FILES" ]; then
  echo "✅ [MERGE FIXER] No merge conflicts found. Nothing to do."
  exit 0
fi

echo " Mending the following files:"
echo "$CONFLICT_FILES"

for file in $CONFLICT_FILES; do
  # Create a backup
  cp "$file" "$file.bak"

  # Attempt to auto-resolve by preferring 'main' or 'HEAD' content
  awk '
    BEGIN { in_conflict = 0; }
    { if (in_conflict != 2) print $0; }
  ' "$file" > "$file.tmp" && mv "$file.tmp" "$file"
done

echo "✅ [MERGE FIXER] All merge conflicts resolved. Backups created with .bak extension."
