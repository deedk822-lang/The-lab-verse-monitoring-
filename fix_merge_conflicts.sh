#!/bin/bash
set -e

echo "🔍 [MERGE FIXER] Starting intelligent merge conflict resolution..."

# Find all files with merge conflict markers
CONFLICT_FILES=$(git diff --name-only --diff-filter=U || true)

if [ -z "$CONFLICT_FILES" ]; then
  echo "✅ [MERGE FIXER] No merge conflicts found. Nothing to do."
  exit 0
fi

echo "🔧 [MERGE FIXER] Mending the following files:"
echo "$CONFLICT_FILES"

# Use a while loop to handle filenames with spaces correctly
while IFS= read -r file; do
  # Create a backup
  cp "$file" "$file.bak"

  # Attempt to auto-resolve by preferring HEAD content over incoming changes
  awk '
    BEGIN { in_conflict = 0; }
    /<<<<<<< HEAD/ { in_conflict = 1; next }
    /=======/      { in_conflict = 2; next }
    />>>>>>>/      { in_conflict = 0; next }
    in_conflict != 2 { print }
  ' "$file" > "$file.tmp" && mv "$file.tmp" "$file"
done <<< "$CONFLICT_FILES"

echo "✅ [MERGE FIXER] All merge conflicts resolved. Backups created with .bak extension."
