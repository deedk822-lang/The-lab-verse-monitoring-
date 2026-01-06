#!/bin/bash
set -euo pipefail

# Configuration
DRY_RUN=false
INTERACTIVE=true
CREATE_BACKUP=true
BACKUP_DIR=".broken_files_backup_$(date +%Y%m%d_%H%M%S)"
LOG_FILE="removed_files_$(date +%Y%m%d_%H%M%S).log"

# Argument parsing (fixed version)
while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --non-interactive)
            INTERACTIVE=false
            shift
            ;;
        --no-backup)
            CREATE_BACKUP=false
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  --dry-run           Show what would be deleted"
            echo "  --non-interactive   Don't ask for confirmation"
            echo "  --no-backup         Don't create backup"
            echo "  -h, --help          Show this help"
            exit 0
            ;;
        *)
            echo "Unknown option: $1" >&2
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Pattern definitions
PATTERNS=(
    "*.pyc"
    "*.pyo"
    "__pycache__"
    "*.swp"
    "*.swo"
    "*~"
    ".DS_Store"
)

EXCLUDE_PATTERNS=(
    ".git"
    ".venv"
    "node_modules"
)

# Build find command safely
FIND_CMD=(find . -type f)
for pattern in "${PATTERNS[@]}"; do
    FIND_CMD+=(-name "$pattern" -o)
done
# Remove trailing -o
unset 'FIND_CMD[-1]'

# Add exclusions
for exclude in "${EXCLUDE_PATTERNS[@]}"; do
    FIND_CMD+=(-not -path "*/$exclude/*")
done

# Add null delimiter for safe processing
FIND_CMD+=(-print0)

echo "🔍 Scanning for broken files..."

# Count files and build list safely
FILE_COUNT=0
FILE_LIST=()
while IFS= read -r -d '' file; do
    FILE_LIST+=("$file")
    ((FILE_COUNT++))
done < <("${FIND_CMD[@]}")

if [ $FILE_COUNT -eq 0 ]; then
    echo "✅ No broken files found"
    exit 0
fi

echo "📋 Found $FILE_COUNT broken file(s):"
printf '  - %s\n' "${FILE_LIST[@]}" | head -20
if [ $FILE_COUNT -gt 20 ]; then
    echo "  ... and $((FILE_COUNT - 20)) more"
fi

# Dry run check
if [ "$DRY_RUN" = true ]; then
    echo ""
    echo "🏃 DRY RUN MODE: No files will be deleted"
    exit 0
fi

# Interactive confirmation
if [ "$INTERACTIVE" = true ]; then
    echo ""
    read -p "❓ Delete these files? [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Cancelled by user"
        exit 0
    fi
fi

# Create backup if requested
if [ "$CREATE_BACKUP" = true ]; then
    echo "💾 Creating backup in $BACKUP_DIR..."
    mkdir -p "$BACKUP_DIR"

    for file in "${FILE_LIST[@]}"; do
        backup_path="$BACKUP_DIR/$(dirname "$file")"
        mkdir -p "$backup_path"
        cp "$file" "$backup_path/" 2>/dev/null || true
    done

    echo "✅ Backup created: $BACKUP_DIR"
fi

# Delete files and log
echo "🗑️  Deleting files..."
DELETED_COUNT=0
FAILED_COUNT=0

for file in "${FILE_LIST[@]}"; do
    if rm -f "$file" 2>/dev/null; then
        echo "$file" >> "$LOG_FILE"
        ((DELETED_COUNT++))
    else
        echo "Failed: $file" >> "$LOG_FILE"
        ((FAILED_COUNT++))
        echo "  ⚠️  Failed to delete: $file"
    fi
done

echo ""
echo "📊 Deletion Summary:"
echo "  Successfully deleted: $DELETED_COUNT"
echo "  Failed: $FAILED_COUNT"
echo "  Log file: $LOG_FILE"

if [ "$CREATE_BACKUP" = true ]; then
    echo "  Backup location: $BACKUP_DIR"
fi

[ $FAILED_COUNT -eq 0 ] && exit 0 || exit 1
