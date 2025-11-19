#!/bin/bash
set -euo pipefail

# Enhanced Package-Lock Conflict Resolver
# Usage: ./fix-package-lock-conflict.sh [--dry-run] [--package-manager npm|yarn|pnpm]

SCRIPT_VERSION="1.2.0"
DRY_RUN=false
PACKAGE_MANAGER="npm"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
case "$1" in
--dry-run)
DRY_RUN=true
echo "🔍 DRY RUN MODE - No changes will be made"
;;
--package-manager)
shift
PACKAGE_MANAGER="$1"
if [[ ! "$PACKAGE_MANAGER" =~ ^(npm|yarn|pnpm)$ ]]; then
echo "❌ ERROR: Invalid package manager. Use: npm, yarn, or pnpm"
exit 1
fi
;;
*)
echo "❌ ERROR: Unknown argument: $1"
echo "Usage: $0 [--dry-run] [--package-manager npm|yarn|pnpm]"
exit 1
;;
esac
shift
done

echo "🔧 Package-Lock Conflict Resolver v$SCRIPT_VERSION"
echo " Package Manager: $PACKAGE_MANAGER"
echo " Dry Run: $DRY_RUN"
echo "========================================"

# Safety checks
check_prerequisites() {
echo "✅ Checking prerequisites..."

# Check if in git repository
if ! git rev-parse --is-inside-work-tree &>/dev/null; then
echo "❌ ERROR: Not in a git repository"
exit 1
fi

# Check if package.json exists
if [[ ! -f package.json ]]; then
echo "❌ ERROR: package.json not found in current directory"
exit 1
fi

# Check for uncommitted changes (except package-lock.json)
if git status --porcelain | grep -v 'package-lock.json' | grep -v 'package-lock.json' | grep -q '.'; then
echo "⚠️ WARNING: Uncommitted changes detected in other files:"
git status --porcelain | grep -v 'package-lock.json'
read -p "Continue anyway? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
echo "❌ Aborted by user"
exit 1
fi
fi

# Check if package.json has conflicts
if grep -q '<<<<<<<' package.json || grep -q '>>>>>>>' package.json; then
echo "❌ ERROR: package.json contains merge conflicts!"
echo " Please resolve package.json conflicts manually first:"
echo " 1. Open package.json in your editor"
echo " 2. Remove conflict markers (<<<<<<<, =======, >>>>>>>)"
echo " 3. Choose the correct dependencies versions"
echo " 4. Run: git add package.json"
exit 1
fi

echo "✅ All prerequisites met"
}

# Verify package manager installation
check_package_manager() {
echo "✅ Checking $PACKAGE_MANAGER installation..."

if ! command -v "$PACKAGE_MANAGER" &>/dev/null; then
echo "❌ ERROR: $PACKAGE_MANAGER not found. Please install it first."
echo " For npm: https://nodejs.org/"
echo " For yarn: npm install -g yarn"
echo " For pnpm: npm install -g pnpm"
exit 1
fi

# Get versions
NODE_VERSION=$(node --version 2>/dev/null || echo "not installed")
NPM_VERSION=$("$PACKAGE_MANAGER" --version 2>/dev/null || echo "not installed")

echo " Node.js version: $NODE_VERSION"
echo " ${PACKAGE_MANAGER^^} version: $NPM_VERSION"

# Version compatibility warnings
if [[ "$NODE_VERSION" =~ v18 ]]; then
echo "⚠️ WARNING: Node.js 18 detected. Consider using Node.js 20+ for better compatibility"
elif [[ "$NODE_VERSION" =~ v16 ]]; then
echo "⚠️ WARNING: Node.js 16 is EOL. Upgrade to Node.js 20+ recommended"
fi
}

# Backup existing files
create_backups() {
echo "✅ Creating backups..."

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR=".package-lock-backups/$TIMESTAMP"

mkdir -p "$BACKUP_DIR"

if [[ -f package-lock.json ]]; then
if $DRY_RUN; then
echo " [DRY RUN] Would backup package-lock.json to $BACKUP_DIR/"
else
cp package-lock.json "$BACKUP_DIR/package-lock.json.backup"
echo " ✅ Backed up package-lock.json to $BACKUP_DIR/"
fi
fi

if [[ -f yarn.lock ]] && [[ "$PACKAGE_MANAGER" == "yarn" ]]; then
if $DRY_RUN; then
echo " [DRY RUN] Would backup yarn.lock to $BACKUP_DIR/"
else
cp yarn.lock "$BACKUP_DIR/yarn.lock.backup"
echo " ✅ Backed up yarn.lock to $BACKUP_DIR/"
fi
fi

if [[ -f pnpm-lock.yaml ]] && [[ "$PACKAGE_MANAGER" == "pnpm" ]]; then
if $DRY_RUN; then
echo " [DRY RUN] Would backup pnpm-lock.yaml to $BACKUP_DIR/"
else
cp pnpm-lock.yaml "$BACKUP_DIR/pnpm-lock.yaml.backup"
echo " ✅ Backed up pnpm-lock.yaml to $BACKUP_DIR/"
fi
fi
}

# Clean node_modules and lock files
clean_environment() {
echo "✅ Cleaning environment..."

# Remove existing lock files
lock_files=()
if [[ "$PACKAGE_MANAGER" == "npm" ]]; then
lock_files=("package-lock.json")
elif [[ "$PACKAGE_MANAGER" == "yarn" ]]; then
lock_files=("yarn.lock")
elif [[ "$PACKAGE_MANAGER" == "pnpm" ]]; then
lock_files=("pnpm-lock.yaml")
fi

for lock_file in "${lock_files[@]}"; do
if [[ -f "$lock_file" ]]; then
if $DRY_RUN; then
echo " [DRY RUN] Would remove $lock_file"
else
rm -f "$lock_file"
echo " ✅ Removed $lock_file"
fi
fi
done

# Optional: Clean node_modules (commented out by default)
# if [[ -d node_modules ]]; then
# if $DRY_RUN; then
# echo " [DRY RUN] Would remove node_modules/"
# else
# rm -rf node_modules/
# echo " ✅ Removed node_modules/"
# fi
# fi
}

# Regenerate lock file
regenerate_lock() {
echo "✅ Regenerating lock file with $PACKAGE_MANAGER..."

if $DRY_RUN; then
echo " [DRY RUN] Would run: $PACKAGE_MANAGER install --package-lock-only"
return 0
fi

case "$PACKAGE_MANAGER" in
npm)
npm install --package-lock-only --ignore-scripts
;;
yarn)
yarn install --ignore-scripts
;;
pnpm)
pnpm install --lockfile-only --ignore-scripts
;;
esac

echo "✅ Successfully regenerated lock file"
}

# Verify integrity
verify_integrity() {
echo "✅ Verifying lock file integrity..."

if $DRY_RUN; then
echo " [DRY RUN] Would verify lock file integrity"
return 0
fi

case "$PACKAGE_MANAGER" in
npm)
if ! npm ls --depth=0 &>/dev/null; then
echo "⚠️ WARNING: Some dependencies may have issues. Check the output above."
read -p "Continue anyway? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
echo "❌ Aborted due to dependency issues"
exit 1
fi
fi
;;
yarn)
if ! yarn check --integrity &>/dev/null; then
echo "⚠️ WARNING: Lock file integrity check failed"
read -p "Continue anyway? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
echo "❌ Aborted due to integrity issues"
exit 1
fi
fi
;;
pnpm)
if ! pnpm validate &>/dev/null; then
echo "⚠️ WARNING: Lock file validation failed"
read -p "Continue anyway? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
echo "❌ Aborted due to validation issues"
exit 1
fi
fi
;;
esac

echo "✅ Lock file integrity verified"
}

# Stage changes
stage_changes() {
echo "✅ Staging changes..."

lock_file=""
case "$PACKAGE_MANAGER" in
npm) lock_file="package-lock.json" ;;
yarn) lock_file="yarn.lock" ;;
pnpm) lock_file="pnpm-lock.yaml" ;;
esac

if $DRY_RUN; then
echo " [DRY RUN] Would run: git add $lock_file"
return 0
fi

if git add "$lock_file"; then
echo "✅ Successfully staged $lock_file"
else
echo "❌ ERROR: Failed to stage $lock_file"
exit 1
fi
}

# Final status check
show_status() {
echo "✅ Final status check..."

if $DRY_RUN; then
echo " [DRY RUN] Would show git status"
return 0
fi

echo "----------------------------------------"
git status --short
echo "----------------------------------------"

echo ""
echo "🎉 SUCCESS! Package lock conflict resolved"
echo ""
echo "Next steps:"
echo "1. Review other conflicted files if any:"
echo " git status"
echo "2. Complete the merge:"
echo " git commit -m \"chore: resolve package-lock.json merge conflict\""
echo "3. Push changes:"
echo " git push origin feat-improve-ci-cd-pipeline"
echo ""
echo "💡 Pro tip: Consider adding this to your .gitattributes:"
echo " package-lock.json merge=ours"
echo " yarn.lock merge=ours"
echo " pnpm-lock.yaml merge=ours"
}

# Main execution
main() {
check_prerequisites
check_package_manager
create_backups
clean_environment
regenerate_lock
verify_integrity
stage_changes
show_status
}

# Run the script
main
