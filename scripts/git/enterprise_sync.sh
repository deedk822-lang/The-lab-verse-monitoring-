#!/bin/bash
# Enterprise Branch Synchronization Engine
# Compliant with: GitOps, Immutable Infrastructure, Audit Requirements

set -euo pipefail

# Configuration
UPSTREAM="main"
MERGE_STRATEGY="ort"  # Ort is the modern recursive, handles renames better
LOG_FILE="git-sync-$(date +%Y%m%d-%H%M%S).log"
CONFLICT_LOG="conflicts-$(date +%Y%m%d-%H%M%S).log"
SLACK_WEBHOOK="${SLACK_WEBHOOK:-}"  # Optional: Team notifications

# Logging Infrastructure
exec 1> >(tee -a "$LOG_FILE")
exec 2> >(tee -a "$LOG_FILE" >&2)

log() {
    echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*"
}

error_exit() {
    log "ERROR: $1"
    # Send alert if Slack configured
    [ -n "$SLACK_WEBHOOK" ] && curl -X POST -H 'Content-type: application/json' \
        --data "{\"text\":\"Git Sync Failed: $1\"}" "$SLACK_WEBHOOK" || true
    exit 1
}

# Dynamic Branch Discovery (Exclude protected/release branches)
discover_branches() {
    # Find branches not yet fully merged into upstream
    git branch -r --no-merged "origin/$UPSTREAM" --format='%(refname:lstrip=3)' | \
        grep -v -E '^(HEAD|main|master|release/.*|hotfix/.*)$' | \
        while read -r branch; do
            # Check if branch is behind upstream
            # behind_count = commits in origin/$UPSTREAM that are NOT in origin/$branch
            behind_count=$(git rev-list --count "origin/$branch..origin/$UPSTREAM" 2>/dev/null || echo "0")
            if [ "$behind_count" -gt 0 ]; then
                echo "$branch:$behind_count"
            fi
        done | sort -t':' -k2 -nr  # Sort by commit drift (most stale first)
}

# Atomic Synchronization with Rollback Capability
sync_branch_atomic() {
    local branch=$1
    local behind_count=$2
    local temp_ref="refs/sync-temp/${branch//\//-}"

    log "🔄 Processing $branch (behind by $behind_count commits)"

    # Create immutable backup reference
    git update-ref "$temp_ref" "origin/$branch"

    # Checkout with detached HEAD to avoid local branch pollution
    git checkout --detach "origin/$branch"

    # Check if GPG signing is enabled/available
    GPG_FLAG=""
    if git config --get user.signingkey > /dev/null; then
        GPG_FLAG="--gpg-sign"
    fi

    # Configure merge strategy for specific file types (reduce conflicts)
    git config merge.ours.driver true  # Preserve ours for specific paths if needed

    if git merge "origin/$UPSTREAM" \
        --no-ff \
        $GPG_FLAG \
        --strategy="$MERGE_STRATEGY" \
        --strategy-option="find-renames=50%" \
        -m "chore(sync): Integrate upstream changes from $UPSTREAM

Batch synchronization operation.
Original branch state preserved at: $temp_ref
Drift metric: $behind_count commits"; then

        # Atomic push (all or nothing across refs)
        # Note: refs/archive/ is used for compliance backup
        git push --atomic origin "HEAD:refs/heads/$branch" "+$temp_ref:refs/archive/$(date +%Y/%m/%d)/${branch//\//-}"

        log "✅ Success: $branch archived and updated"
        return 0
    else
        # Rollback on failure
        log "❌ Conflict detected in $branch"
        echo "$branch" >> "$CONFLICT_LOG"

        # Reset to pre-merge state
        git merge --abort 2>/dev/null || true
        git checkout "$UPSTREAM"

        # Notify without failing entire batch
        return 1
    fi
}

# Main Execution
main() {
    log "🚀 Starting Enterprise Git Synchronization"

    # Safety: Ensure we're not in the middle of a previous operation
    if [ -d ".git/rebase-merge" ] || [ -d ".git/MERGE_HEAD" ]; then
        error_exit "Repository in incomplete state. Resolve previous operation first."
    fi

    # Update upstream reference
    git fetch origin "$UPSTREAM:$UPSTREAM" || error_exit "Failed to update $UPSTREAM"

    # Process queue
    discover_branches | while IFS=: read -r branch behind; do
        sync_branch_atomic "$branch" "$behind" || true  # Continue on individual failure
    done

    # Generate Report
    log "📊 Synchronization Complete"
    log "Log file: $LOG_FILE"
    if [ -f "$CONFLICT_LOG" ]; then
        log "⚠️  Conflicts detected in: $(wc -l < "$CONFLICT_LOG") branches"
        log "Review: $CONFLICT_LOG"
    fi

    # Return to upstream branch
    git checkout "$UPSTREAM"
}

main "$@"
