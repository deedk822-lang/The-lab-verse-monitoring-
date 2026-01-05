#!/bin/bash
set -e

DRY_RUN=false
INTERACTIVE=true
EXCLUDE_PATTERNS=(
  './.git/*'
  './node_modules/*'
  './__tests__/*'
  '*.test.js'
  '*.spec.js'
)

# Parse command-line arguments
for arg in "$@"; do
  case $arg in
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    --non-interactive)
      INTERACTIVE=false
      shift
      ;;
    *)
      # Unknown option
      ;;
  esac
done

echo "🔍 [FILE CLEANER] Identifying and removing out-of-scope files..."

# Define patterns for out-of-scope files
PATTERNS=(
  "*asana*"
  "*g20*"
  "*rankyak*"
  "*mock*"
  "*simulation*"
)

# Build the find command with exclusions
EXCLUDE_ARGS=()
for pattern in "${EXCLUDE_PATTERNS[@]}"; do
  EXCLUDE_ARGS+=(-not -path "$pattern")
done

# Find files matching the patterns
FILES_TO_DELETE=$(find . -type f \( -name "${PATTERNS[0]}" $(printf -- ' -o -name "%s"' "${PATTERNS[@]:1}") \) "${EXCLUDE_ARGS[@]}")

if [ -z "$FILES_TO_DELETE" ]; then
  echo "✅ [FILE CLEANER] No out-of-scope files found."
  exit 0
fi

echo "The following files will be deleted:"
echo "$FILES_TO_DELETE"

if [ "$DRY_RUN" = true ]; then
  echo "DRY RUN: No files will be deleted."
  exit 0
fi

if [ "$INTERACTIVE" = true ]; then
  read -p "Are you sure you want to delete these files? (y/N) " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborting."
    exit 1
  fi
fi

# Delete the files
# Use xargs to handle a large number of files
echo "$FILES_TO_DELETE" | xargs rm -f

echo "✅ [FILE CLEANER] Out-of-scope files removed."
