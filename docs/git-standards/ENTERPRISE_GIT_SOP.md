# Enterprise Git Branch Synchronization Standard Operating Procedure (SOP)

**Document Classification:** Technical Standard
**Version:** 1.0
**Scope:** Shared Branch Maintenance & Upstream Synchronization
**Compliance:** ISO 27001 (Change Management), SOX (Audit Trail)

---

## 1. Pre-Execution Safety Protocol
Before executing any branch synchronization, verify system state to prevent data loss.

### Safety Check Items:
- **Working Tree Integrity:** Ensure no uncommitted or unstashed changes.
- **Remote Connectivity:** Verify reachability of the `origin` remote.
- **Backup Reference Creation:** Create an immutable recovery point (tag) before operations.
- **Disk Space Validation:** Ensure sufficient space for large merges and worktrees.

*Automation for these checks can be found in `scripts/git/pre_sync_checks.sh`.*

---

## 2. Standard Operating Procedure: Merge-Based Synchronization

### Phase 1: Canonical Branch Update
Update the golden `main` branch using fast-forward-only to ensure linear history on the canonical branch.

```bash
# Lock mechanism to prevent concurrent modifications
git config --local core.locked true

git checkout main
git fetch origin --prune

# Verify main is not ahead of remote (prevent divergence)
LOCAL_MAIN=$(git rev-parse main)
REMOTE_MAIN=$(git rev-parse origin/main)

if [ "$LOCAL_MAIN" != "$REMOTE_MAIN" ]; then
    echo "⚠️  WARNING: Local main diverges from origin. Investigate before proceeding."
    exit 1
fi

# Fast-forward only - never rewrite published history
git merge --ff-only origin/main
git config --local core.locked false
```

### Phase 2: Feature Branch Synchronization (Non-Destructive)
Use merge strategy with explicit merge commits (`--no-ff`) to preserve context and audit trails.

```bash
# Define your target branch
feature_branch="feature/your-branch-name"

# GPG-signed merge commit for non-repudiation
git merge origin/main \
    --no-ff \
    --no-edit \
    --gpg-sign \
    -m "Merge main into ${feature_branch}

Source: origin/main
Target: ${feature_branch}
Operator: $(git config user.name)
Timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)
Ticket: [INSERT_JIRA_TICKET]"

# Push with lease (fail if remote changed during operation)
git push --atomic origin "$feature_branch" --force-with-lease
```

---

## 3. Enterprise Automation: Scalable Batch Processing
**Critical Enhancement:** Dynamically detect stale branches rather than hardcoding names. This prevents human error and scales to hundreds of repositories.

The automated engine (`scripts/git/enterprise_sync.sh`) performs:
- **Dynamic Branch Discovery:** Identifies branches behind upstream.
- **Isolation:** Uses detached HEAD or worktrees to prevent local pollution.
- **Atomic Operations:** Ensures all-or-nothing updates across references.
- **Logging & Auditing:** Comprehensive logs for SIEM ingestion.

---

## 4. Conflict Resolution Runbook (Global Standards)
When automatic merging fails, follow this standardized resolution protocol:

### 4.1 Isolation Protocol
```bash
# Create isolated environment for conflict resolution
CONFLICT_BRANCH="fix/resolve-conflict-$(date +%s)"
git checkout -b "$CONFLICT_BRANCH" origin/main
git merge origin/feature/problematic-branch --no-ff
```

### 4.2 Resolution Matrix
| Conflict Type | Resolution Authority | Evidence Required |
| :--- | :--- | :--- |
| **Source Code** | Original Author + Tech Lead | CI Test Pass + Code Review |
| **Configuration** | DevOps/Platform Team | Diff review + Staging validation |
| **Documentation** | Technical Writer | Markdown lint + Link check |
| **Dependencies** | Security Team + Author | `npm audit` / `pip check` clean |

### 4.3 Resolution Execution
```bash
# After manual conflict resolution
git add -A
git commit --no-edit --gpg-sign  # Preserve merge commit message + sign

# Verification before push
git diff origin/main..HEAD --stat  # Review scope of changes
git log --oneline --left-right origin/main...HEAD  # Review commit topology

# Protected push with verification
git push -u origin "$CONFLICT_BRANCH"
# Create PR for peer review before merging to main
```

---

## 5. Verification & Quality Assurance
Post-synchronization validation ensures repository integrity.

### Validation Suite:
1. **Merge Commit Verification:** Ensure explicit merge commits exist.
2. **GPG Signature Verification:** Audit for non-repudiation.
3. **File System Check:** Run `git fsck --full --strict`.
4. **CI Status Check:** Verify branch health via `gh pr checks`.

*Automation for validation can be found in `scripts/git/validate_sync.sh`.*

---

## 6. Communication Protocol
After batch operations, notify stakeholders using the following template:

**Subject:** [ACTION REQUIRED] Branch Synchronization Complete - ${REPO_NAME}

**Affected Branches:**
<!-- List from conflict log -->

**Action Items:**
1. **For Authors:** Verify your feature branches function correctly in staging.
2. **For QA:** Regression test affected components.
3. **For DevOps:** Monitor CI/CD pipelines for increased load.

**Rollback:** If critical issues arise, recover using:
`git fetch origin refs/archive/$(date +%Y/%m/%d)/<branch-name> && git reset --hard FETCH_HEAD`

---

## 7. Compliance & Security Notes
- **Immutable History:** The `refs/archive/` pattern ensures compliance with WORM (Write Once Read Many) requirements.
- **Non-Repudiation:** Mandate `--gpg-sign` for merge commits in regulated environments.
- **Least Privilege:** Use `--force-with-lease` instead of `--force` to prevent accidental overwrites.
- **Observability:** Structured logs for SIEM ingestion.

---

## 8. Quick Reference: Decision Matrix
| Scenario | Strategy | Risk Level |
| :--- | :--- | :--- |
| **Shared feature branch** | Merge (`--no-ff`) | Low |
| **Local only, pre-push** | Rebase (interactive) | Minimal |
| **Release branch hotfix** | Cherry-pick + Merge | Medium |
| **Long-lived integration** | Merge with `ort` strategy | Low |
| **Public OSS contribution** | Rebase + Force Push | High (coordinate) |

---
**Audit Hash:** `$(git rev-parse HEAD | sha256sum | head -c 16)`
