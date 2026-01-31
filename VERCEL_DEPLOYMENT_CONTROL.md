# 🚀 Vercel Deployment Control Guide

**Status**: ✅ **Automatic PR Deployments DISABLED**  
**Last Updated**: January 27, 2026

---

## ✅ What's Been Configured

### **1. Smart Deployment Control** (`vercel.json`)

```json
{
  "ignoreCommand": "bash scripts/vercel-ignore-build.sh",
  "github": {
    "silent": true,
    "autoJobCancelation": true,
    "autoAlias": false
  }
}
```

**What this does**:
- ✅ **Runs custom check** before every deployment
- ✅ **Silent mode** - No GitHub comments on PRs
- ✅ **Auto-cancels** redundant deployments
- ✅ **No auto-aliases** for preview deployments

### **2. Ignored Build Step** (`scripts/vercel-ignore-build.sh`)

**Deployment ONLY happens when**:
- ✅ Branch is `main`, `master`, or `production`
- ✅ Actual code files changed (not just docs/configs)
- ✅ Commit doesn't contain `[skip-vercel]` or `[vercel-skip]`

**Deployment is SKIPPED for**:
- ⏭️ Pull request branches
- ⏭️ Documentation-only changes (`.md`, `.txt` files)
- ⏭️ Config changes (`.yml`, `.yaml`, `.sh` files)
- ⏭️ Directory changes (`docs/`, `k8s/`, `scripts/`, `monitoring/`)
- ⏭️ Commits with `[skip-vercel]` flag

### **3. File Ignore List** (`.vercelignore`)

**Vercel will NOT trigger deployments for changes to**:
- Documentation (`*.md`, `README*`, `docs/`)
- Tests (`tests/`, `*.test.*`, `*.spec.*`)
- CI/CD configs (`.github/`, `.circleci/`)
- Docker files (`Dockerfile`, `docker-compose.yml`)
- Kubernetes manifests (`k8s/`, `*.yaml`)
- Scripts (`scripts/`, `*.sh`)
- Development tools (`.vscode/`, `.idea/`)
- Database files (`*.sql`, `*.db`)
- Monitoring configs (`monitoring/`, `prometheus/`, `grafana/`)

---

## 📋 Deployment Decision Flow

```
Commit pushed to GitHub
         │
         ▼
   Is it main/production branch? ──── NO ──► ⏭️ SKIP
         │
        YES
         │
         ▼
   Does commit have [skip-vercel]? ── YES ──► ⏭️ SKIP
         │
        NO
         │
         ▼
   Did code files change? ──────────── NO ──► ⏭️ SKIP
         │                        (only docs/configs)
        YES
         │
         ▼
    🚀 DEPLOY!
```

---

## 🎯 How to Use

### **Force Skip Deployment**
```bash
git commit -m "Update README [skip-vercel]"
# or
git commit -m "[vercel-skip] Fix typos"
```

### **Force Deployment on Any Branch**
Currently blocked by the ignore script. To enable:

**Option 1**: Edit `scripts/vercel-ignore-build.sh`
```bash
# Comment out the branch check:
# if [[ "$BRANCH" != "main" && "$BRANCH" != "master" && "$BRANCH" != "production" ]]; then
#     echo "⏭️  Skipping: Not on main/production branch"
#     exit 0
# fi
```

**Option 2**: Temporarily disable ignore command in Vercel dashboard
1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Select your project
3. Settings → Git → Ignored Build Step
4. Temporarily remove or modify

### **Deploy Specific PR**
If you need to deploy a PR for testing:

1. **Merge to `main`** (recommended)
2. **Create temporary production branch**:
   ```bash
   git checkout -b production-test-pr-123
   git push origin production-test-pr-123
   ```
   This will trigger deployment because branch name contains "production"

3. **Use Vercel CLI** (manual):
   ```bash
   npm i -g vercel
   vercel --prod  # Deploy current branch
   ```

---

## ⚙️ Additional Vercel Dashboard Settings

### **Recommended Settings**

Navigate to: **Vercel Dashboard → Project → Settings → Git**

1. **Production Branch**: `main` (or `master`)
   - Only this branch deploys to production URL

2. **Preview Deployments**: 
   - ✅ Enable for: **Production Branch Only**
   - ❌ Disable for: **All Other Branches**

3. **Deployment Protection**:
   - ✅ Enable **Deploy Hooks** protection
   - ✅ Enable **Vercel Authentication** for previews

4. **Build & Development Settings**:
   - Ignored Build Step: `bash scripts/vercel-ignore-build.sh`
   - ✅ Override default behavior

### **Screenshot Reference**
```
Settings → Git
├── Production Branch: main
├── Preview Deployments
│   ├── ✅ Enabled for production branch
│   └── ❌ Disabled for other branches  ← IMPORTANT!
└── Ignored Build Step
    └── bash scripts/vercel-ignore-build.sh
```

---

## 🔧 Troubleshooting

### **Problem: PRs still deploying**

**Solution 1**: Verify Vercel dashboard settings
```
Vercel Dashboard → Project → Settings → Git → Preview Deployments
Set to: "Production Branch Only"
```

**Solution 2**: Check ignore script permissions
```bash
chmod +x scripts/vercel-ignore-build.sh
git add scripts/vercel-ignore-build.sh
git commit -m "fix: Make vercel ignore script executable"
```

**Solution 3**: Manually disable in Vercel
```
Vercel Dashboard → Project → Settings → Git
Ignored Build Step → Test with PR branch
Should return exit code 0 (skip)
```

### **Problem: Main branch not deploying**

**Solution**: Check script logs in Vercel build output
```bash
# Look for:
🔍 Checking if build should be skipped...
📍 Branch: main
✅ Building: Code changes detected
```

If showing "Skipping", verify you changed actual code files:
```bash
# This WILL deploy:
git commit -m "feat: Update API endpoint" api/server.py

# This will SKIP:
git commit -m "docs: Update README" README.md
```

### **Problem: Want to temporarily enable all PR deployments**

**Quick Fix** (emergency only):
```bash
# Edit vercel.json, remove ignoreCommand:
{
  "buildCommand": "pip install -r requirements.txt",
  // "ignoreCommand": "bash scripts/vercel-ignore-build.sh",  ← Comment out
  ...
}
```

Or in Vercel Dashboard:
```
Settings → Git → Ignored Build Step
Clear the field temporarily
```

---

## 📊 Monitoring Deployment Activity

### **View Deployment History**
```bash
# Install Vercel CLI
npm i -g vercel

# Login
vercel login

# List deployments
vercel ls

# View logs for specific deployment
vercel logs [deployment-url]
```

### **GitHub Actions Integration**
If you want GitHub Actions to notify about skipped deployments:

```yaml
# .github/workflows/vercel-notify.yml
name: Vercel Deployment Notification

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  notify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Check if Vercel will deploy
        run: |
          if bash scripts/vercel-ignore-build.sh; then
            echo "✅ Vercel deployment will be SKIPPED for this PR"
            echo "Reason: Non-production branch or docs-only changes"
          else
            echo "🚀 Vercel deployment will PROCEED"
          fi
```

---

## 🎯 Best Practices

### **1. Use Descriptive Commit Messages**
```bash
# Good - Clear intent
git commit -m "docs: Update API documentation [skip-vercel]"

# Better - Automatic skip for docs
git commit -m "docs: Update API documentation"
# (automatically skipped by .vercelignore)
```

### **2. Group Non-Code Changes**
```bash
# Batch docs/config changes together
git add README.md docs/ k8s/
git commit -m "chore: Update documentation and configs"
# Single skip instead of multiple attempts
```

### **3. Separate Code and Docs PRs**
```bash
# PR #1: Code changes (will deploy to main)
feat: Add new API endpoint

# PR #2: Documentation (won't deploy)
docs: Document new API endpoint
```

### **4. Use Feature Flags for Testing**
Instead of deploying every PR:
```python
# Use feature flags in your code
if os.getenv("FEATURE_NEW_ENDPOINT") == "true":
    # New feature code
```

Deploy once to main, toggle features in Vercel environment variables.

---

## 📈 Cost Savings Estimate

### **Before** (All PRs deploy)
- Average: 50 PRs/month
- Build time: 5 min/deployment
- Cost: ~$20-50/month (depending on plan)

### **After** (Only main branch + code changes)
- Average: 10 deployments/month
- Build time: 5 min/deployment  
- Cost: ~$5-10/month
- **Savings: 60-80% reduction** 💰

---

## 🔗 Resources

- **Vercel Docs**: [Ignored Build Step](https://vercel.com/docs/projects/overview#ignored-build-step)
- **Vercel Docs**: [Git Integration](https://vercel.com/docs/deployments/git)
- **GitHub**: [Repository Settings](https://github.com/deedk822-lang/The-lab-verse-monitoring-/settings)
- **Vercel Dashboard**: [Project Settings](https://vercel.com/dashboard)

---

## ✅ Verification Checklist

- [x] `vercel.json` configured with `ignoreCommand`
- [x] `scripts/vercel-ignore-build.sh` created and executable
- [x] `.vercelignore` file configured
- [x] GitHub `silent` mode enabled
- [x] Auto-alias disabled for PRs
- [ ] Verify in Vercel dashboard: Preview deployments = "Production Branch Only"
- [ ] Test with sample PR (should skip)
- [ ] Test with main branch code change (should deploy)

---

**🎉 You're all set! Vercel will now only deploy when it actually matters.**

**Questions?** Check the troubleshooting section or review the Vercel deployment logs.
