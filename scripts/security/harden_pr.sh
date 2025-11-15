#!/bin/bash
# Harden changed files in a PR and commit them
# Designed to run in CI or locally before pushing

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🔒 PR Security Hardening${NC}"
echo "================================"

# Check for MOONSHOT_API_KEY
if [ -z "${MOONSHOT_API_KEY:-}" ]; then
    echo -e "${RED}❌ MOONSHOT_API_KEY environment variable not set${NC}"
    exit 1
fi

# Get changed files (works in CI or locally)
if [ -n "${GITHUB_BASE_REF:-}" ]; then
    # Running in GitHub Actions
    echo -e "${BLUE}📋 Detecting changed files from PR...${NC}"
    BASE_REF="origin/${GITHUB_BASE_REF}"
    CHANGED_FILES=$(git diff --name-only "$BASE_REF" HEAD || echo "")
else
    # Running locally - compare with main/master
    echo -e "${BLUE}📋 Detecting changed files (local mode)...${NC}"
    
    # Try to find the default branch
    if git rev-parse --verify origin/main >/dev/null 2>&1; then
        BASE_REF="origin/main"
    elif git rev-parse --verify origin/master >/dev/null 2>&1; then
        BASE_REF="origin/master"
    else
        echo -e "${YELLOW}⚠️  Could not find main/master branch. Using HEAD~1${NC}"
        BASE_REF="HEAD~1"
    fi
    
    CHANGED_FILES=$(git diff --name-only "$BASE_REF" HEAD || echo "")
fi

if [ -z "$CHANGED_FILES" ]; then
    echo -e "${YELLOW}⚠️  No changed files detected${NC}"
    exit 0
fi

echo -e "${GREEN}Found changed files:${NC}"
echo "$CHANGED_FILES" | sed 's/^/  • /'

# Filter for security-critical files
CRITICAL_PATTERNS="\.py$|\.yml$|\.yaml$|Dockerfile|\.env\.example$|\.sh$|\.bash$|\.js$|\.ts$|\.go$|\.conf$"
CRITICAL_FILES=$(echo "$CHANGED_FILES" | grep -E "$CRITICAL_PATTERNS" || echo "")

if [ -z "$CRITICAL_FILES" ]; then
    echo -e "${YELLOW}⚠️  No security-critical files changed${NC}"
    exit 0
fi

echo ""
echo -e "${BLUE}🔍 Security-critical files to harden:${NC}"
echo "$CRITICAL_FILES" | sed 's/^/  • /'

# Create temporary directory for hardened files
TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR" EXIT

# Harden each file
HARDENED_COUNT=0
FAILED_COUNT=0

cd "$REPO_ROOT"

while IFS= read -r file; do
    if [ ! -f "$file" ]; then
        echo -e "${YELLOW}⚠️  Skipping deleted file: $file${NC}"
        continue
    fi
    
    echo ""
    echo -e "${BLUE}🔒 Hardening: $file${NC}"
    
    if python3 "$SCRIPT_DIR/secure_file.py" "$file" 2>&1; then
        echo -e "${GREEN}✅ Hardened: $file${NC}"
        ((HARDENED_COUNT++))
    else
        echo -e "${RED}❌ Failed to harden: $file${NC}"
        ((FAILED_COUNT++))
    fi
done <<< "$CRITICAL_FILES"

echo ""
echo "================================"
echo -e "${BLUE}📊 Summary${NC}"
echo "  Hardened: $HARDENED_COUNT"
echo "  Failed:   $FAILED_COUNT"
echo "================================"

# Check if any files were modified
if [ -n "$(git status --porcelain)" ]; then
    echo ""
    echo -e "${GREEN}✅ Files were hardened and modified${NC}"
    
    # Show what changed
    echo ""
    echo -e "${BLUE}📝 Modified files:${NC}"
    git status --short
    
    # In CI, commit and push the changes
    if [ -n "${CI:-}" ]; then
        echo ""
        echo -e "${BLUE}🚀 Committing hardened files...${NC}"
        
        git config user.name "Security Hardening Bot"
        git config user.email "security@labverse.local"
        
        git add -A
        git commit -m "🔒 Auto-harden security-critical files

Applied OWASP best-practice hardening using Moonshot AI:
- Removed hardcoded credentials
- Added input validation
- Implemented secure defaults
- Enhanced error handling

Files hardened: $HARDENED_COUNT
Files failed: $FAILED_COUNT
"
        
        echo -e "${GREEN}✅ Changes committed${NC}"
    else
        echo ""
        echo -e "${YELLOW}⚠️  Running locally - changes not committed${NC}"
        echo -e "${YELLOW}    Review the changes and commit manually if satisfied${NC}"
    fi
else
    echo ""
    echo -e "${YELLOW}⚠️  No files were modified (already secure or no changes needed)${NC}"
fi

if [ $FAILED_COUNT -gt 0 ]; then
    echo ""
    echo -e "${RED}❌ Some files failed to harden${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}✅ PR security hardening complete${NC}"
exit 0

