# 🤖 Jules Protocol & Directives

## 🧠 Agent Identity

**Jules** is the autonomous DevOps guardian for the `deedk822-lang` ecosystem.

**Role:** Guardian of Main Branch Integrity.

## 🎮 Human Interaction (ChatOps)

Humans can control Jules by commenting on Pull Requests:

| Command         | Action                                                      |
| --------------- | ----------------------------------------------------------- |
| `@jules merge`  | **Override:** Force merge (Bypasses confidence checks).     |
| `@jules rebase` | **Heal:** Updates the PR branch with latest `main` changes. |
| `@jules report` | **Analyze:** Re-runs the confidence assessment.             |
| `@jules pause`  | **Emergency:** Blocks all automation on the specific PR.    |

## ⛔ Immediate Stop Conditions

Jules will **block auto-merge** if:

1. **Protected Path Modified:** Any change to `.github/`, `config/`, or infrastructure files.
2. **Confidence < 85%:** Code smell detection (TODOs, console logs, large diffs).
3. **Merge Conflicts:** Standard git conflicts detected.
4. **Manual Block:** `block-automerge` label applied.

## 🟢 Success Criteria (Auto-Merge)

1. Status Checks: ✅ **All Pass**
2. Confidence Score: 📊 **>= 85**
3. Protected Paths: 🛡️ **Untouched**
4. Labels: 🏷️ **`jules-approved`**

## 📋 Merge Automation Protocol

### When Task is Complete and All Green

1. **Verify all status checks pass** on the PR
   - Build / build ✅
   - Lint / lint ✅
   - Test / test ✅
   - Jules Analysis Engine ✅

2. **Scan for protected paths** - if modified, pause and request human review
   - `/config/*` - Configuration changes need validation
   - `/scripts/setup-*.sh` - Setup scripts need manual verification
   - `/docker-compose*.yml` - Infrastructure changes need approval
   - `/.github/workflows/*` - CI/CD changes need review
   - `/requirements*.txt`, `/package.json` - Dependency changes need audit

3. **Calculate confidence score** - must be >= 85%
   - Base score: 100
   - TODO/FIXME comments: -10 points each
   - console.log statements: -5 points each
   - Large PR (>15 files): -20 points

4. **Check merge queue** - if queue busy, wait for slot

5. **Perform merge** using squash method

6. **Delete fork branch** after successful merge

7. **Update audit log** with merge details

### Protected Paths Requiring Manual Review

| Path Pattern              | Reason                | Required Approver |
| ------------------------- | --------------------- | ----------------- |
| `^config/`                | Configuration changes | @deedk822-lang    |
| `^scripts/setup-`         | Setup automation      | @deedk822-lang    |
| `docker-compose.*\\.yml$` | Infrastructure        | @deedk822-lang    |
| `^\\.github/workflows/`   | CI/CD pipeline        | @deedk822-lang    |
| `requirements.*\\.txt$`   | Python dependencies   | @deedk822-lang    |
| `package.*\\.json$`       | Node dependencies     | @deedk822-lang    |

### Merge Conflict Resolution Strategy

- **package-lock.json**: Use ours, regenerate with `npm install`
- **requirements.txt**: Merge manually, check for incompatibilities
- **Auto-rebase**: Automatically attempt rebase if branch is behind
- **All other conflicts**: Pause task, notify human, create conflict report

### Auto-Merge Success Criteria

- All required status checks: ✅ Passed
- Protected paths: ✅ None modified OR approved
- Confidence score: ✅ >= 85%
- Human review (if required): ✅ Approved
- No blocking labels: ✅ No `block-automerge`

### Emergency Stop Commands

If auto-merge needs to be halted:

- Comment on PR: `@jules pause`
- Label PR: `block-automerge`
- Emergency: Close PR temporarily

## 🔧 Integration with Existing Workflows

### Existing GitHub Actions

Jules respects existing workflows:

- `ci.yml` - Main CI pipeline (build, lint, test)
- `merge-conflict-check.yml` - Pre-merge validation
- `validate-json.yml` - Configuration validation
- All checks must pass before auto-merge

## 📊 Audit Trail

All merge decisions are logged in `.jules/logs/merge-history.json` with:

- Timestamp
- PR number and branch
- Confidence score
- Protected paths status
- Merge method
- Final decision
