#!/bin/bash
# Pre-flight Safety Check Script
# Execute before any merge operations

set -euo pipefail

echo "🔍 Executing Pre-Synchronization Safety Checks..."

# 1. Working Tree Integrity
if [ -n "$(git status --porcelain)" ]; then
    echo "❌ ERROR: Working tree is not clean. Commit or stash changes before proceeding."
    exit 1
fi

# 2. Remote Connectivity Verification
if ! git ls-remote origin HEAD &>/dev/null; then
    echo "❌ ERROR: Cannot reach origin remote. Check network/VPN."
    exit 1
fi

# 3. Backup Reference Creation (Immutable Recovery Point)
BACKUP_TAG="backup/pre-sync/$(date +%Y%m%d-%H%M%S)"
git tag -a "$BACKUP_TAG" -m "Pre-synchronization backup: $(git rev-parse --abbrev-ref HEAD)"
echo "✅ Backup tag created: $BACKUP_TAG"

# 4. Disk Space Validation (Prevent corruption during large merges)
REQUIRED_GB=2
AVAILABLE_GB=$(df -BG . | tail -1 | awk '{print $4}' | tr -d 'G')
if [ "$AVAILABLE_GB" -lt "$REQUIRED_GB" ]; then
    echo "❌ ERROR: Insufficient disk space. Required: ${REQUIRED_GB}GB, Available: ${AVAILABLE_GB}GB"
    exit 1
fi

echo "✅ All safety checks passed. Proceeding with synchronization..."
