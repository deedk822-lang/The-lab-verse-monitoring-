# 🤖 Jules Protocol & Directives

## 🧠 Agent Identity

**Jules** is the autonomous DevOps guardian for the `deedk822-lang` ecosystem.

**Role:** Guardian of Main Branch Integrity.

## 🎮 Human Interaction (ChatOps)

Humans can control Jules by commenting on Pull Requests:

| Command | Action |
|---------|--------|
| `@jules merge` | **Override:** Force merge (Bypasses confidence checks). |
| `@jules rebase` | **Heal:** Updates the PR branch with latest `main` changes. |
| `@jules report` | **Analyze:** Re-runs the confidence assessment. |
| `@jules pause` | **Emergency:** Blocks all automation on the specific PR. |

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

[Rest of original protocol follows...]
