#!/usr/bin/env bash
# repo-cleanup.sh
# Organize repository: rename problematic files, create docs structure, move scripts, remove placeholders.
# Non-interactive mode:
#   DRY_RUN=yes  -> show actions but don't perform git operations
#
# Run: chmod +x repo-cleanup.sh && ./repo-cleanup.sh

set -euo pipefail

DRY_RUN="${DRY_RUN:-no}"

GREEN='\033[0;32m'
NC='\033[0m'

run_or_echo() {
  if [ "$DRY_RUN" = "yes" ]; then
    echo "[DRY RUN] $*"
  else
    eval "$@"
  fi
}

echo -e "${GREEN}🧹 REPOSITORY CLEANUP & ORGANIZATION${NC}"
echo ""

# Step 1: Create directory structure
echo "Creating directories..."
dirs=( "docs/deployment" "docs/guides" "docs/architecture" "docs/quickstart" "docs/testing" "scripts/ci" "scripts/deployment" "scripts/testing" "config/docker" "config/monitoring" "agents" )
for d in "${dirs[@]}"; do
  run_or_echo "mkdir -p \"$d\""
done

# Step 2: Safe rename function
safe_rename() {
  src="$1"
  dest="$2"
  if [ -e "$src" ]; then
    run_or_echo "git mv -f \"$src\" \"$dest\" 2>/dev/null || (mkdir -p \"$(dirname "$dest")\" && mv \"$src\" \"$dest\")"
    echo "Renamed: $src -> $dest"
  fi
}

# List of renames (add/remove as needed)
echo "Renaming files..."
safe_rename "Start MCP server" "docs/quickstart/start-mcp-server.md"
safe_rename "Script's" "docs/scripts-inventory.txt"
safe_rename "Routes utility" "docs/architecture/routes-utility.md"
safe_rename "Configure connector  .env" "config/.env.connector.example"
safe_rename "Docker compose YAML" "config/docker/docker-compose-example.yml"
safe_rename "Bash_run" "scripts/bash-run.sh"
safe_rename "Smoke test" "scripts/testing/smoke-test.sh"
# ... add further renames as necessary (this script contains the most common ones)

# Step 3: Move other docs if present
echo "Moving documentation files..."
safe_rename "DEPLOYMENT_GUIDE.md" "docs/deployment/DEPLOYMENT_GUIDE.md"
safe_rename "QUICKSTART.md" "docs/quickstart/QUICKSTART.md"
safe_rename "TESTING_README.md" "docs/testing/README.md"

# Step 4: Remove zero-byte or placeholder files
echo "Removing empty placeholder files..."
candidates=( "doc" "git init" "alert manager" "grafana" "prometheus" )
for c in "${candidates[@]}"; do
  if [ -f "$c" ] && [ ! -s "$c" ]; then
    run_or_echo "git rm --ignore-unmatch \"$c\" || rm -f \"$c\""
    echo "Removed empty: $c"
  fi
done

# Step 5: Create docs index
echo "Creating docs/INDEX.md..."
run_or_echo "mkdir -p docs"
run_or_echo "cat > docs/INDEX.md <<'EOF'
# Documentation Index

- Quickstart: docs/quickstart
- Deployment: docs/deployment
- Guides: docs/guides
- Architecture: docs/architecture
- Testing: docs/testing
EOF
"

# Step 6: Stage & commit
echo "Staging and committing changes..."
if [ "$DRY_RUN" = "yes" ]; then
  echo "[DRY RUN] git add -A"
  echo "[DRY RUN] git commit -m 'chore(repo): reorganize repository structure' || true"
else
  git add -A
  if git diff --cached --quiet; then
    echo "No changes to commit."
  else
    git commit -m "🧹 chore(repo): reorganize repository structure and fix filenames"
    echo "Committed repository reorganization."
  fi
fi

echo ""
echo -e "${GREEN}✅ REPO CLEANUP COMPLETE${NC}"
echo ""
