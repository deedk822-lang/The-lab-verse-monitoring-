#!/bin/bash

# Validate JSON Files Script
# Run this manually: ./scripts/validate-json.sh

set -e

echo "🔍 JSON Validation Suite"
echo "════════════════════════════════════════"
echo ""

# Function to validate a single JSON file
validate_json() {
  local file=$1
  local errors=0
  
  echo "Checking: $file"
  
  # Check if file exists
  if [ ! -f "$file" ]; then
    echo "❌ File not found: $file"
    return 1
  fi
  
  # Check for merge conflict markers
  if grep -q "^<<<<<<< \|^======= \|^>>>>>>> " "$file"; then
    echo "  ❌ Merge conflict markers found"
    errors=$((errors + 1))
  fi
  
  # Check for branch names (common in merge conflicts)
  if grep -qE "^ *(main|feature/|fix/|hotfix/|release/|TheLapVerseCore\.ts) *$" "$file"; then
    echo "  ❌ Branch name found in file (possible unresolved merge conflict)"
    errors=$((errors + 1))
  fi
  
  # Validate JSON syntax with Node.js
  if ! node -e "JSON.parse(require('fs').readFileSync('$file', 'utf8'))" 2>/dev/null; then
    echo "  ❌ Invalid JSON syntax"
    errors=$((errors + 1))
  fi
  
  # Check for duplicate keys (requires Python)
  if command -v python3 &> /dev/null; then
    if ! python3 -c "
import json
import sys

def check_duplicates(pairs):
    keys = {}
    for key, value in pairs:
        if key in keys:
            print(f'  ❌ Duplicate key: {key}')
            sys.exit(1)
        keys[key] = value
    return keys

try:
    with open('$file', 'r') as f:
        json.load(f, object_pairs_hook=check_duplicates)
except:
    sys.exit(1)
" 2>/dev/null; then
      errors=$((errors + 1))
    fi
  fi
  
  if [ $errors -eq 0 ]; then
    echo "  ✅ Valid"
    return 0
  else
    return 1
  fi
}

# Find all JSON files
echo "Finding JSON files..."
JSON_FILES=$(find . -name "*.json" -not -path "*/node_modules/*" -not -path "*/.next/*" -not -path "*/dist/*" -not -path "*/.git/*")

if [ -z "$JSON_FILES" ]; then
  echo "⚠️  No JSON files found"
  exit 0
fi

echo "Found $(echo "$JSON_FILES" | wc -l) JSON files"
echo ""

# Validate each file
FAILED_FILES=()
for file in $JSON_FILES; do
  if ! validate_json "$file"; then
    FAILED_FILES+=("$file")
  fi
  echo ""
done

# Summary
echo "════════════════════════════════════════"
if [ ${#FAILED_FILES[@]} -eq 0 ]; then
  echo "✅ ALL JSON FILES ARE VALID"
  echo "════════════════════════════════════════"
  exit 0
else
  echo "❌ VALIDATION FAILED"
  echo "════════════════════════════════════════"
  echo ""
  echo "Failed files:"
  for file in "${FAILED_FILES[@]}"; do
    echo "  - $file"
  done
  echo ""
  echo "Please fix these files before committing."
  exit 1
fi
