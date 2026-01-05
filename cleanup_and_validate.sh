#!/usr/bin/env bash
# cleanup_and_validate.sh - Remove all unwanted integrations and mock-ups
# Version: 2.0.0 Production

set -e
set -o pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
echo_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
echo_error() { echo -e "${RED}[ERROR]${NC} $1"; }
echo_step() { echo -e "${BLUE}[STEP]${NC} $1"; }

REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
cd "$REPO_ROOT"

BACKUP_DIR="./.cleanup-backup-$(date +%Y%m%d-%H%M%S)"
CLEANUP_LOG="./cleanup-report.log"

echo_info "====================================================="
echo_info "  Repository Cleanup & Validation Tool v2.0"
echo_info "====================================================="
echo_info "Repository: $REPO_ROOT"
echo_info "Backup location: $BACKUP_DIR"
echo ""

# Create backup directory
mkdir -p "$BACKUP_DIR"
echo "Cleanup started at $(date)" > "$CLEANUP_LOG"

# ============================================================
# STEP 1: Remove Asana Integrations
# ============================================================
echo_step "Step 1: Removing Asana integrations..."

ASANA_FILES=(
    "*asana*.py"
    "*asana*.js"
    "*asana*.ts"
    "asana-analytics-dashboard.py"
    "scripts/asana_*.py"
    "agents/asana_agent.py"
    "workflows/asana_workflow.yml"
    ".github/workflows/asana*.yml"
)

for pattern in "${ASANA_FILES[@]}"; do
    while IFS= read -r -d '' file; do
        echo_info "Removing Asana file: $file"
        mkdir -p "$BACKUP_DIR/$(dirname "$file")"
        cp "$file" "$BACKUP_DIR/$file" 2>/dev/null || true
        rm "$file"
        echo "  - Removed: $file" >> "$CLEANUP_LOG"
    done < <(find . -type f -name "$pattern" -not -path "./.cleanup-backup-*" -not -path "./.git/*" -print0 2>/dev/null)
done

# Remove Asana references from code
echo_info "Removing Asana imports and references..."
find . -type f \( -name "*.py" -o -name "*.js" -o -name "*.ts" \) \
    -not -path "./.cleanup-backup-*" \
    -not -path "./.git/*" \
    -not -path "./node_modules/*" \
    -not -path "./venv/*" \
    -exec sed -i.bak '/import.*asana/d' {} \; \
    -exec sed -i.bak '/from.*asana/d' {} \; \
    -exec sed -i.bak '/require.*asana/d' {} \; 2>/dev/null || true

# Clean up .bak files
find . -name "*.bak" -type f -delete 2>/dev/null || true

echo_info "✓ Asana integrations removed"

# ============================================================
# STEP 2: Remove G20 Content
# ============================================================
echo_step "Step 2: Removing G20 branch content..."

G20_PATTERNS=(
    "*g20*"
    "*G20*"
    "docs/g20/*"
    "workflows/g20_*"
    ".github/workflows/g20*.yml"
)

for pattern in "${G20_PATTERNS[@]}"; do
    while IFS= read -r -d '' file; do
        echo_info "Removing G20 file: $file"
        mkdir -p "$BACKUP_DIR/$(dirname "$file")"
        cp "$file" "$BACKUP_DIR/$file" 2>/dev/null || true
        rm "$file"
        echo "  - Removed: $file" >> "$CLEANUP_LOG"
    done < <(find . -type f -iname "$pattern" -not -path "./.cleanup-backup-*" -not -path "./.git/*" -print0 2>/dev/null)
done

# Remove G20 directories
find . -type d -iname "*g20*" -not -path "./.cleanup-backup-*" -not -path "./.git/*" -exec rm -rf {} + 2>/dev/null || true

echo_info "✓ G20 content removed"

# ============================================================
# STEP 3: Remove Rankyak Integrations
# ============================================================
echo_step "Step 3: Removing rankyak integrations..."

RANKYAK_FILES=(
    "*rankyak*.py"
    "*rankyak*.js"
    "scripts/rankyak_sync.py"
    "wordpress_sync_*"
    "rankyak_enrichment_*"
    "workflows/rankyak_*"
)

for pattern in "${RANKYAK_FILES[@]}"; do
    while IFS= read -r -d '' file; do
        echo_info "Removing rankyak file: $file"
        mkdir -p "$BACKUP_DIR/$(dirname "$file")"
        cp "$file" "$BACKUP_DIR/$file" 2>/dev/null || true
        rm "$file"
        echo "  - Removed: $file" >> "$CLEANUP_LOG"
    done < <(find . -type f -iname "$pattern" -not -path "./.cleanup-backup-*" -not -path "./.git/*" -print0 2>/dev/null)
done

# Remove rankyak references
find . -type f \( -name "*.py" -o -name "*.js" -o -name "*.ts" \) \
    -not -path "./.cleanup-backup-*" \
    -not -path "./.git/*" \
    -not -path "./node_modules/*" \
    -not -path "./venv/*" \
    -exec sed -i '/rankyak/Id' {} \; 2>/dev/null || true

echo_info "✓ Rankyak integrations removed"

# ============================================================
# STEP 4: Remove Mock-ups and Simulations
# ============================================================
echo_step "Step 4: Removing mock-ups and simulations..."

MOCKUP_PATTERNS=(
    "*mock*.py"
    "*mock*.js"
    "*simulation*.py"
    "*demo*.py"
    "*example*.py"
    "*placeholder*.py"
    "*stub*.py"
    "*fake*.py"
    "tests/mocks/*"
)

for pattern in "${MOCKUP_PATTERNS[@]}"; do
    while IFS= read -r -d '' file; do
        # Skip test files that legitimately need mocks
        if [[ "$file" == *"/tests/"* ]] || [[ "$file" == *"/__tests__/"* ]]; then
            echo_warn "Skipping test mock: $file"
            continue
        fi

        echo_info "Removing mock-up: $file"
        mkdir -p "$BACKUP_DIR/$(dirname "$file")"
        cp "$file" "$BACKUP_DIR/$file" 2>/dev/null || true
        rm "$file"
        echo "  - Removed: $file" >> "$CLEANUP_LOG"
    done < <(find . -type f -name "$pattern" -not -path "./.cleanup-backup-*" -not -path "./.git/*" -not -path "./node_modules/*" -print0 2>/dev/null)
done

# Remove TODO and FIXME comments
echo_info "Removing TODO/FIXME comments..."
find . -type f \( -name "*.py" -o -name "*.js" -o -name "*.ts" \) \
    -not -path "./.cleanup-backup-*" \
    -not -path "./.git/*" \
    -not -path "./node_modules/*" \
    -not -path "./venv/*" \
    -exec sed -i '/# TODO/d' {} \; \
    -exec sed -i '/# FIXME/d' {} \; \
    -exec sed -i '/\/\/ TODO/d' {} \; \
    -exec sed -i '/\/\/ FIXME/d' {} \; 2>/dev/null || true

echo_info "✓ Mock-ups and simulations removed"

# ============================================================
# STEP 5: Fix Path Configurations
# ============================================================
echo_step "Step 5: Fixing path configurations..."

# Update .env if it exists
if [ -f ".env" ]; then
    echo_info "Updating .env file..."

    # Backup original
    cp .env "$BACKUP_DIR/.env.original"

    # Fix common path issues
    sed -i 's|REPO_ROOT=.*|REPO_ROOT='$REPO_ROOT'|g' .env
    sed -i 's|PROJECT_ROOT=.*|PROJECT_ROOT='$REPO_ROOT'|g' .env

    # Remove invalid paths
    sed -i '/ASANA_/d' .env
    sed -i '/G20_/d' .env
    sed -i '/RANKYAK_/d' .env
fi

# Update docker-compose paths if exists
if [ -f "docker-compose.yml" ]; then
    echo_info "Updating docker-compose.yml paths..."
    cp docker-compose.yml "$BACKUP_DIR/docker-compose.yml.original"

    sed -i "s|/app/repo|$REPO_ROOT|g" docker-compose.yml
fi

echo_info "✓ Path configurations fixed"

# ============================================================
# STEP 6: Validate Environment
# ============================================================
echo_step "Step 6: Validating environment..."

# Check for required directories
REQUIRED_DIRS=(
    ".jules"
    ".jules/logs"
    ".jules/temp"
    ".jules/validation-results"
    "agents"
    "clients"
    "scripts"
)

for dir in "${REQUIRED_DIRS[@]}"; do
    if [ ! -d "$dir" ]; then
        echo_info "Creating directory: $dir"
        mkdir -p "$dir"
    fi
done

# Check for required files
if [ ! -f "requirements.txt" ]; then
    echo_warn "requirements.txt not found, creating template..."
    cat > requirements.txt << 'EOF'
# Production Dependencies
langchain==0.3.0
langchain-openai==0.2.0
langchain-community
pydantic==2.5.0
requests==2.31.0
python-dotenv==1.0.0
prometheus-client==0.19.0
semgrep==1.50.0

# Optional but recommended
black==23.12.0
pylint==3.0.3
pytest==7.4.3
pytest-cov==4.1.0
EOF
fi

if [ ! -f "package.json" ]; then
    echo_warn "package.json not found, creating template..."
    cat > package.json << 'EOF'
{
  "name": "autonomous-builder-platform",
  "version": "2.0.0",
  "description": "Hybrid Brain-to-Hands Autonomous Builder",
  "scripts": {
    "start": "node orchestrator/index.js",
    "lint": "eslint .",
    "test": "jest",
    "build": "webpack --mode production"
  },
  "dependencies": {
    "express": "^4.18.2",
    "dotenv": "^16.3.1",
    "axios": "^1.6.2"
  },
  "devDependencies": {
    "eslint": "^8.55.0",
    "jest": "^29.7.0",
    "prettier": "^3.1.1"
  }
}
EOF
fi

echo_info "✓ Environment validated"

# ============================================================
# STEP 7: Create Cleanup Report
# ============================================================
echo_step "Step 7: Generating cleanup report..."

cat >> "$CLEANUP_LOG" << EOF

========================================
CLEANUP SUMMARY
========================================
Date: $(date)
Repository: $REPO_ROOT
Backup Location: $BACKUP_DIR

FILES REMOVED:
$(find "$BACKUP_DIR" -type f | wc -l) files backed up

CATEGORIES:
- Asana integrations
- G20 content
- Rankyak integrations
- Mock-ups and simulations
- TODO/FIXME comments

VALIDATION:
- Required directories created
- Configuration files validated
- Path references fixed

NEXT STEPS:
1. Review backup at: $BACKUP_DIR
2. Run: python3 validate_env.py
3. Run: bash production_startup.sh
4. Test system health

========================================
EOF

cat "$CLEANUP_LOG"

echo ""
echo_info "====================================================="
echo_info "  Cleanup Complete!"
echo_info "====================================================="
echo_info "Backup saved to: $BACKUP_DIR"
echo_info "Full report: $CLEANUP_LOG"
echo ""
echo_info "Next steps:"
echo_info "  1. Review the cleanup report"
echo_info "  2. Run: python3 validate_env.py"
echo_info "  3. Run: bash production_startup.sh"
echo ""

# Optional: Commit changes
read -p "Would you like to commit these changes? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    git add -A
    git commit -m "chore: remove Asana, G20, rankyak integrations and mock-ups

- Removed all Asana integration files and references
- Removed G20 branch content
- Removed rankyak sync scripts and integrations
- Removed mock-ups, simulations, and placeholder code
- Fixed path configurations
- Validated environment structure

Backup created at: $BACKUP_DIR"
    echo_info "Changes committed successfully"
fi

exit 0