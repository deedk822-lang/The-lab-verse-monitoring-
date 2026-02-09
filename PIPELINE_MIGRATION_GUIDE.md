# CI/CD Pipeline Optimization - Migration Guide

## 🎯 Problem Solved
Your PR had **12 checks queued** because you had too many workflows running simultaneously. This caused:
- ⏰ Massive queue times (hours of waiting)
- 💰 Wasted GitHub Actions minutes
- 🔄 Redundant checks (type-check ran 3 times!)

## ✅ New Optimized Pipeline

**File:** `.github/workflows/main-ci.yml`

### Pipeline Structure:
```text
Stage 1 (2 min)  → Quick Validation + Lint
                ↓
Stage 2 (3 min)  → Security Scans
                ↓
Stage 3 (5 min)  → Tests (with DB services)
                ↓
Stage 4 (5 min)  → Docker Build
                ↓
Stage 5          → Optional (performance, etc.)
```

**Total Runtime:** ~15 minutes (vs. hours of queuing!)

## 🗑️ Workflows to Disable

Move these files to `.github/workflows.disabled/`:

1. `ci-cd.yml` - Replaced by main-ci.yml
2. `ci.yml` - Replaced by main-ci.yml
3. `type-safe-ci.yml` - Consolidated into main-ci.yml
4. `llm-code-review.yml` - Keep separate, but optimize (see below)
5. `pr-fix-agent.yml` - Keep separate, but optimize (see below)
6. `kimi-enhancer.yml` / `kimi-enhancer.yaml` - Keep one, disable duplicate

### Keep These (But Update):
- `jules-governance.yml` - Runs separately on label
- `jules-actuator.yml` - Runs on specific events
- `framer-governance.yml` - Runs on specific paths
- `kaggle-intelligence.yml` - Scheduled daily
- `performance.yml` - Now conditional in main pipeline

## 🚀 Quick Migration Steps

```bash
# 1. Create backup directory
mkdir -p .github/workflows.disabled

# 2. Move old workflows
mv .github/workflows/ci-cd.yml .github/workflows.disabled/
mv .github/workflows/ci.yml .github/workflows.disabled/
mv .github/workflows/type-safe-ci.yml .github/workflows.disabled/

# 3. Move duplicate kimi file (verify .yml version exists first)
if [ -f ".github/workflows/kimi-enhancer.yml" ]; then
  mv .github/workflows/kimi-enhancer.yaml .github/workflows.disabled/  # Keep the .yml version
fi

# 4. Commit the new pipeline
git add .github/workflows/main-ci.yml
git add .github/workflows.disabled/
git commit -m "feat: optimize CI/CD pipeline - consolidate workflows"
git push
```

## 🔧 Workflow-Specific Optimizations

### For LLM-Powered Code Review:
Add this to the top of `llm-code-review.yml`:

```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

# Only run when explicitly requested
on:
  workflow_dispatch:
  pull_request:
    types: [labeled]

jobs:
  collect-findings:
    if: contains(github.event.pull_request.labels.*.name, 'llm-review')
    # ... rest of job
```

### For PR Fix Agent:
Update `pr-fix-agent.yml`:

```yaml
concurrency:
  group: pr-fix-${{ github.event.pull_request.number }}
  cancel-in-progress: true

on:
  workflow_dispatch:  # Manual only
  pull_request:
    types: [labeled]

jobs:
  analyze-and-fix:
    if: contains(github.event.pull_request.labels.*.name, 'auto-fix')
    # ... rest of job
```

## 📊 Expected Results

### Before:
```text
✗ 12 checks queued
✗ 3 checks running
✗ Wait time: 2-4 hours
✗ Duplicate work
```

### After:
```text
✓ 1 main pipeline (5 jobs)
✓ All checks run in 15 minutes
✓ Proper dependencies
✓ Smart caching
✓ Concurrent where safe
```

## 🎛️ Advanced: Conditional Workflows

The new pipeline includes smart conditionals:

```yaml
# Run performance tests only when labeled
if: contains(github.event.pull_request.labels.*.name, 'performance')

# Skip draft PRs
if: github.event.pull_request.draft == false

# Only deploy on push to main
if: github.event_name == 'push' && github.ref == 'refs/heads/main'
```

## 🔐 Security Considerations

All security checks still run, but now:
- ✅ Run in parallel when possible
- ✅ Don't block each other
- ✅ Upload artifacts for review
- ✅ Non-blocking unless critical

## 📝 Customization

### To add a new check:
1. Determine which stage it belongs to
2. Add as a step in existing job (if fast)
3. Or create new job with proper `needs:` dependency

### To make a check required:
Update branch protection rules:
```text
Settings → Branches → Branch protection rules → main
→ Require status checks: "Quick Validation", "Test Suite"
```

## 🆘 Troubleshooting

### If tests still queue:
1. Check concurrent workflow runs: Settings → Actions → General
2. Increase runner limits (for paid plans)
3. Use `concurrency:` groups more aggressively

### If specific job fails:
1. Check job logs in Actions tab
2. Tests have proper dependencies (`needs:` field)
3. Secrets are configured correctly

## 📚 Resources

- [GitHub Actions Concurrency](https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions#concurrency)
- [Reusable Workflows](https://docs.github.com/en/actions/using-workflows/reusing-workflows)
- [Caching Dependencies](https://docs.github.com/en/actions/using-workflows/caching-dependencies-to-speed-up-workflows)

---

## ✨ Bonus: Performance Tips

1. **Use caching:**
   - Python: `cache: 'pip'` in setup-python
   - Docker: `cache-from: type=gha`
   - Node: `cache: 'npm'` in setup-node

2. **Parallel tests:**
   - Use `pytest-xdist` with `-n auto`
   - Splits tests across CPU cores

3. **Matrix strategy:**
   - Only test multiple Python versions on main push
   - PRs test single version

4. **Artifacts:**
   - Upload only what's needed for debugging
   - Set short retention periods (7 days)

---

**Need help?** Check workflow runs in the Actions tab for detailed logs!
