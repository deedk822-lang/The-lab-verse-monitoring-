#!/usr/bin/env bash
# security-cleanup.sh
# Safe security inspection & removal of tracked environment files.
# Non-interactive by default; set env vars to change behavior:
#   FORCE_ROTATED=yes    -> skip rotation confirmation prompt
#   DELETE_PLACEHOLDERS=yes -> delete small placeholder files automatically
#   DRY_RUN=yes          -> do not make any git changes (just print what would be done)
#
# Run: chmod +x security-cleanup.sh && ./security-cleanup.sh

set -euo pipefail

RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m'

DRY_RUN="${DRY_RUN:-no}"
FORCE_ROTATED="${FORCE_ROTATED:-no}"
DELETE_PLACEHOLDERS="${DELETE_PLACEHOLDERS:-no}"

echo -e "${GREEN}🔒 CRITICAL SECURITY AUDIT & CLEANUP${NC}"
echo ""

FOUND_SECRETS=0

# Helper to run or echo
run_or_echo() {
  if [ "$DRY_RUN" = "yes" ]; then
    echo "[DRY RUN] $*"
  else
    eval "$@"
  fi
}

# Step 1: Inspect env files
echo "Step 1: Inspecting environment files..."
env_files=( ".env.local" "Configure connector  .env" "cp .env.example .env" ".env" ".env.*" )
for f in "${env_files[@]}"; do
  if [ -f "$f" ]; then
    echo -e "${RED}⚠️  FOUND: $f${NC}"
    echo "Content preview (first 20 lines, values redacted):"
    head -n 20 "$f" | sed 's/\(.*=\).*/\1[REDACTED]/' || true
    FOUND_SECRETS=1
  fi
done
echo ""

# Step 2: Run Gitleaks if available
echo "Step 2: Running Gitleaks (if installed)..."
if command -v gitleaks >/dev/null 2>&1; then
  echo "Scanning repository..."
  if [ "$DRY_RUN" = "yes" ]; then
    echo "[DRY RUN] gitleaks detect --source . --report-path gitleaks-report.json --no-git || true"
  else
    gitleaks detect --source . --report-path gitleaks-report.json --no-git || true
    if [ -s gitleaks-report.json ]; then
      echo -e "${RED}🚨 Gitleaks found possible secrets — see gitleaks-report.json${NC}"
      FOUND_SECRETS=1
    else
      echo -e "${GREEN}✅ No findings in gitleaks-report.json (or file empty)${NC}"
    fi
  fi
else
  echo -e "${YELLOW}⚠️  gitleaks not found. Add it or rely on CI scan.${NC}"
fi
echo ""

# Step 3: If secrets found, require rotation confirmation
if [ "$FOUND_SECRETS" -eq 1 ]; then
  echo -e "${RED}🚨 SECRETS DETECTED OR SUSPICIOUS FILES PRESENT${NC}"
  if [ "$FORCE_ROTATED" = "yes" ]; then
    echo "FORCE_ROTATED set — proceeding under assumption secrets have been rotated."
  else
    read -r -p "Have you rotated all secrets (yes to continue)? " ROTATED
    if [ "$ROTATED" != "yes" ]; then
      echo -e "${RED}Aborting: rotate secrets first.${NC}"
      exit 1
    fi
  fi
fi

# Step 4: Remove specific files from git tracking (keep local copies)
echo "Step 4: Removing sensitive files from Git tracking (keeps local copies)..."
tracked_files=( ".env.local" "Configure connector  .env" "cp .env.example .env" )
for tf in "${tracked_files[@]}"; do
  if git ls-files --error-unmatch "$tf" >/dev/null 2>&1; then
    run_or_echo "git rm --cached --ignore-unmatch \"$tf\" || true"
    echo "  • Untracked from git: $tf"
  else
    echo "  • Not tracked (or does not exist): $tf"
  fi
done
echo ""

# Step 5: Merge '. gitignore' into .gitignore if present
if [ -f ". gitignore" ]; then
  echo "Step 5: Merging '. gitignore' into .gitignore..."
  run_or_echo "cat '. gitignore' >> .gitignore"
  run_or_echo "git rm --ignore-unmatch '. gitignore' || true"
  echo "  • Merged and removed '. gitignore'"
fi
echo ""

# Step 6: Detect placeholder files
echo "Step 6: Placeholder files detected (review before deletion):"
placeholders=( "doc" "git init" "alert manager" "Routes utility" "Script's" "Python. venv" )
to_delete=()
for file in "${placeholders[@]}"; do
  if [ -f "$file" ]; then
    size=$(wc -c < "$file" || echo 0)
    echo "  - $file ($size bytes)"
    if [ "$size" -lt 200 ]; then
      head -n 5 "$file" | sed 's/^/    /'
    fi
    if [ "$DELETE_PLACEHOLDERS" = "yes" ]; then
      to_delete+=("$file")
    fi
  fi
done

if [ "${#to_delete[@]}" -gt 0 ]; then
  echo "Deleting small placeholder files..."
  for d in "${to_delete[@]}"; do
    run_or_echo "git rm --ignore-unmatch \"$d\" || rm -f \"$d\" || true"
    echo "  • Deleted $d"
  done
fi

echo ""

# Step 7: Ensure comprehensive .gitignore
echo "Step 7: Updating .gitignore..."
run_or_echo "cat >> .gitignore << 'EOF'

# SECURITY: do not commit secrets
.env
.env.*
.env.local
.env.production
.env.development
.env.test
*.env
!.env.example
Configure*.env
cp*.env
gitleaks-report.json

# OS/IDE
.DS_Store
Thumbs.db
.vscode/
.idea/
*.swp

# Python/Node
venv/
env/
__pycache__/
node_modules/

# Build outputs
dist/
build/
*.egg-info/

EOF
"

run_or_echo "git add .gitignore || true"
echo -e "${GREEN}✅ .gitignore updated (or dry-run shown)${NC}"
echo ""

# Step 8: Commit changes
echo "Step 8: Commit changes (if any)..."
if [ "$DRY_RUN" = "yes" ]; then
  echo "[DRY RUN] git commit -m 'chore(security): remove tracked env, update .gitignore' || true"
else
  if git diff --cached --quiet; then
    echo "No staged changes to commit."
  else
    git commit -m "🔒 chore(security): remove tracked env files and update .gitignore" || true
    echo -e "${GREEN}Committed security changes${NC}"
  fi
fi

# Final message
echo ""
echo "=========================================="
echo "🎯 SECURITY CLEANUP STEP COMPLETE"
echo "=========================================="
echo ""
echo "Next recommended steps:"
echo "- Verify secrets are rotated in provider consoles"
echo "- Run git-secret purge (see purge-secrets-from-history.sh)"
echo "- Push commits (git push origin main) or open a PR"
echo ""
