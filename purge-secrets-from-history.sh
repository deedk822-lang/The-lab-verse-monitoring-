#!/usr/bin/env bash
# purge-secrets-from-history.sh
# Rewrites git history to remove sensitive files or replace secrets.
#
# Non-interactive mode options:
#   CONFIRM_ROTATION=yes   -> skip rotation confirmation
#   CONFIRM_BACKUP=yes     -> skip backup confirmation
#   METHOD=1|2             -> 1 = git-filter-repo (recommended), 2 = BFG
#   REPLACE_FILE=/path/to/replace-file.txt  -> replace-text file for git-filter-repo
#   SECRETS_FILE=/path/to/secrets.txt       -> secrets list for BFG
#   PUSH_NOW=yes           -> automatically push mirrored repo (requires remote access)
#
# IMPORTANT: Ensure all secrets have been rotated BEFORE using this script.

set -euo pipefail

METHOD="${METHOD:-1}"
CONFIRM_ROTATION="${CONFIRM_ROTATION:-no}"
CONFIRM_BACKUP="${CONFIRM_BACKUP:-no}"
REPLACE_FILE="${REPLACE_FILE:-/tmp/secrets-to-replace.txt}"
SECRETS_FILE="${SECRETS_FILE:-/tmp/secrets-to-remove.txt}"
PUSH_NOW="${PUSH_NOW:-no}"

echo "🗑️  GIT HISTORY SECRET PURGING"
echo "================================"
echo ""

if [ "${CONFIRM_ROTATION}" != "yes" ]; then
  read -r -p "Have you rotated ALL secrets? (yes to continue): " ROT
  if [ "$ROT" != "yes" ]; then
    echo "Aborting. Rotate secrets first."
    exit 1
  fi
fi

if [ "${CONFIRM_BACKUP}" != "yes" ]; then
  read -r -p "Have you backed up the repository directory? (yes to continue): " BUP
  if [ "$BUP" != "yes" ]; then
    echo "Aborting. Create a backup first."
    exit 1
  fi
fi

if [ "$METHOD" = "1" ]; then
  echo "Using git-filter-repo (recommended)..."
  if ! command -v git-filter-repo >/dev/null 2>&1; then
    echo "git-filter-repo not installed. Installing via pip..."
    pip3 install --user git-filter-repo
    export PATH="$HOME/.local/bin:$PATH"
  fi

  echo "Creating backup copy..."
  cd ..
  REPO_NAME=$(basename "$OLDPWD")
  BACKUP_DIR="${REPO_NAME}-BACKUP-$(date +%Y%m%d-%H%M%S)"
  cp -r "$REPO_NAME" "${BACKUP_DIR}"
  echo "Backup created: ../${BACKUP_DIR}"
  cd "$REPO_NAME"

  echo "Removing specific paths from history (invert paths)..."
  # Paths to remove
  git-filter-repo --invert-paths \
    --path .env.local \
    --path "Configure connector  .env" \
    --path "cp .env.example .env" \
    --force

  if [ -f "$REPLACE_FILE" ] && [ -s "$REPLACE_FILE" ]; then
    echo "Applying replace-text to redact inline secrets..."
    git-filter-repo --replace-text "$REPLACE_FILE" --force
    echo "Replace-text applied."
  else
    echo "No replace-text file provided or file empty. Skipping replace-text."
    echo "If you need to redact literal secret strings, populate: $REPLACE_FILE"
    cat > "$REPLACE_FILE" <<'EOF'
# Example format for git-filter-repo --replace-text
# secret_value==>[REDACTED_SECRET]
# Add one replacement per line.
EOF
    echo "Template written to $REPLACE_FILE"
  fi

  echo "Expire reflog and run gc..."
  git reflog expire --expire=now --all
  git gc --prune=now --aggressive

  echo ""
  echo "Pushing changes is destructive. To push now set PUSH_NOW=yes and ensure you are ready."
  if [ "$PUSH_NOW" = "yes" ]; then
    echo "Forcing push to origin --all and tags..."
    git push origin --force --all
    git push origin --force --tags
    echo "Remote updated (force push). ALL COLLABORATORS must re-clone."
  else
    echo "To apply to remote: git push origin --force --all && git push origin --force --tags"
  fi

elif [ "$METHOD" = "2" ]; then
  echo "Using BFG Repo-Cleaner..."
  if ! command -v java >/dev/null 2>&1; then
    echo "Java not installed. Install Java to use BFG."
    exit 1
  fi

  # Download BFG if needed
  if [ ! -f "bfg.jar" ]; then
    echo "Downloading bfg..."
    curl -L https://repo1.maven.org/maven2/com/madgag/bfg/1.14.0/bfg-1.14.0.jar -o bfg.jar
  fi

  ORIGIN_URL=$(git remote get-url origin)
  cd ..
  REPO_NAME=$(basename "$OLDPWD")
  MIRROR_DIR="${REPO_NAME}-mirror"
  rm -rf "$MIRROR_DIR"
  git clone --mirror "$ORIGIN_URL" "$MIRROR_DIR"
  cd "$MIRROR_DIR"

  # Prepare secrets file
  if [ ! -f "$SECRETS_FILE" ]; then
    cat > "$SECRETS_FILE" <<'EOF'
# Add plain secrets here, one per line, to remove via BFG
#sk-prod-xxx
#AKIA...
EOF
    echo "Template secrets file created at $SECRETS_FILE — edit with actual secrets before continuing."
    read -r -p "Edit $SECRETS_FILE now and press ENTER to continue..." || true
  fi

  echo "Running BFG..."
  java -jar ../bfg.jar --replace-text "$SECRETS_FILE" .
  java -jar ../bfg.jar --delete-files .env.local --delete-files "Configure connector  .env" .

  git reflog expire --expire=now --all
  git gc --prune=now --aggressive

  echo ""
  echo "To apply changes push from the mirror repo:"
  echo "  cd ../$MIRROR_DIR"
  echo "  git push --force"
  if [ "$PUSH_NOW" = "yes" ]; then
    (cd "../$MIRROR_DIR" && git push --force)
  fi
else
  echo "Invalid METHOD. Use METHOD=1 or METHOD=2"
  exit 1
fi

echo ""
echo "=========================================="
echo "✅ SECRET PURGING PROCESS COMPLETE"
echo "=========================================="
echo ""
