#!/usr/bin/env bash
set -euo pipefail

REPO_URL="https://github.com/zai-org/Open-AutoGLM.git"
DEFAULT_BRANCH="main"

# Optional override:
#   export AUTOGLM_COMMIT=<40char_sha_or_main>
AUTOGLM_COMMIT="${AUTOGLM_COMMIT:-$DEFAULT_BRANCH}"

PACKAGE_DIR="autoglm_sa"
REPO_DIR="$PACKAGE_DIR/Open-AutoGLM"

rm -rf "$PACKAGE_DIR" "$PACKAGE_DIR.tar.gz"
mkdir -p "$REPO_DIR"

# Resolve "main" -> exact SHA (reproducible tarball)
if [[ "$AUTOGLM_COMMIT" == "$DEFAULT_BRANCH" ]]; then
  AUTOGLM_COMMIT="$(git ls-remote --heads "$REPO_URL" "refs/heads/$DEFAULT_BRANCH" | awk '{print $1}')"
fi

# Validate SHA
if [[ ! "$AUTOGLM_COMMIT" =~ ^[a-f0-9]{40}$ ]]; then
  echo "❌ Invalid commit hash: $AUTOGLM_COMMIT"
  exit 1
fi

echo "📥 Fetching Open-AutoGLM @ ${AUTOGLM_COMMIT:0:8} ..."

git init "$REPO_DIR" >/dev/null
git -C "$REPO_DIR" remote add origin "$REPO_URL"
git -C "$REPO_DIR" fetch --depth 1 origin "$AUTOGLM_COMMIT"
git -C "$REPO_DIR" checkout -q FETCH_HEAD

PINNED_SHA="$(git -C "$REPO_DIR" rev-parse HEAD)"
echo "$PINNED_SHA" > "$PACKAGE_DIR/AUTOGLM_VERSION.txt"

cp start_autoglm.sh "$PACKAGE_DIR/"
cp config.env "$PACKAGE_DIR/"

echo "📦 Creating package..."
tar -czf "$PACKAGE_DIR.tar.gz" "$PACKAGE_DIR"

echo "✅ Package created: $PACKAGE_DIR.tar.gz"
tar -tzf "$PACKAGE_DIR.tar.gz" | head
