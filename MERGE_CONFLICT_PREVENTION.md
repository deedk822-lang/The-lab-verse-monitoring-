# 🛡️ Merge Conflict Prevention & Resolution Guide

## 🔍 What Happened

The `package.json` file became corrupted due to **unresolved merge conflicts** from multiple branches modifying the same file simultaneously. This resulted in:

- ❌ Invalid JSON syntax (duplicate keys, branch names embedded in file)
- ❌ CI/CD pipeline failures (`npm error EJSONPARSE`)
- ❌ Deployment blocked

---

## ✅ Prevention Systems Implemented

### 1. **GitHub Actions - Automatic Validation**

#### `.github/workflows/validate-json.yml`

Runs on every PR and push to validate:
- ✅ JSON syntax is valid
- ✅ No merge conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`)
- ✅ No duplicate keys in package.json
- ✅ No branch names accidentally committed
- ✅ All required fields present

**Triggers:**
- Every pull request
- Every push to main/protected branches
- Any change to `.json` files

#### `.github/workflows/merge-conflict-check.yml`

Runs on all PRs to:
- ✅ Detect merge conflict markers
- ✅ Validate JSON in all files
- ✅ Check for duplicate keys
- ✅ Prevent corrupted files from being merged

---

### 2. **Git Hooks - Local Validation**

#### `.husky/pre-commit`

Runs **before every commit** to:
- ✅ Validate package.json syntax
- ✅ Check for merge conflicts
- ✅ Validate all staged JSON files
- ✅ Prevent bad commits from being created

**Installation:**
```bash
npm install  # Automatically installs hooks via postinstall
```

**Manual installation:**
```bash
npm run prepare  # Sets up husky
```

---

### 3. **Manual Validation Script**

#### `scripts/validate-json.sh`

Run anytime to check all JSON files:

```bash
chmod +x scripts/validate-json.sh
./scripts/validate-json.sh
```

**Checks:**
- ✅ All JSON files have valid syntax
- ✅ No merge conflict markers
- ✅ No duplicate keys
- ✅ No branch names in files

---

## 🚨 How to Resolve Merge Conflicts (If They Happen)

### Step 1: Identify the Conflict

```bash
git status
# Shows: both modified: package.json
```

### Step 2: Open the File

```bash
cat package.json
```

Look for conflict markers:
```json
  "version": "1.0.0",
```

### Step 3: Resolve Manually

**Option A: Keep incoming changes**
```bash
git checkout --theirs package.json
```

**Option B: Keep current changes**
```bash
git checkout --ours package.json
```

**Option C: Manual merge**
1. Open `package.json` in your editor
2. Remove conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`)
3. Choose which version of each conflicting section to keep
4. Save the file

### Step 4: Validate JSON

```bash
# Test if JSON is valid
node -e "JSON.parse(require('fs').readFileSync('package.json', 'utf8'))"

# Or use jq
jq empty package.json

# Or run validation script
./scripts/validate-json.sh
```

### Step 5: Complete the Merge

```bash
git add package.json
git commit -m "fix: resolve package.json merge conflict"
git push
```

---

## 🎯 Best Practices to Avoid Conflicts

### 1. **Single Source of Truth**

✅ **DO:**
```bash
# Update base branch first
git checkout main
git pull origin main

# Create feature branch
git checkout -b feature/my-feature

# Make changes
# ...

# Commit and push
git add .
git commit -m "feat: my feature"
git push origin feature/my-feature
```

❌ **DON'T:**
```bash
# Creating multiple branches from same base without syncing
git checkout -b feature-1
# ... make changes to package.json ...

git checkout -b feature-2  # Still on old base!
# ... make more changes to package.json ...
# This will cause conflicts!
```

---

### 2. **Regular Synchronization**

```bash
# Before making changes, always sync:
git checkout main
git pull origin main

# Rebase your feature branch
git checkout feature/my-feature
git rebase main

# Resolve any conflicts immediately
```

---

### 3. **Small, Focused PRs**

✅ **DO:**
- One feature per PR
- Merge quickly (don't let PRs sit)
- Rebase on main before merging

❌ **DON'T:**
- Create 10 PRs all modifying package.json
- Let PRs sit unmerged for days
- Ignore merge conflicts

---

### 4. **Use the Validation Tools**

**Before committing:**
```bash
./scripts/validate-json.sh
```

**Before creating PR:**
```bash
npm run build  # Ensure builds succeed
npm run lint   # Ensure linting passes
npm test       # Ensure tests pass
```

**After merging:**
```bash
# Verify CI passes
# Check GitHub Actions tab
```

---

## 🔧 Troubleshooting

### Error: "npm error EJSONPARSE"

**Cause:** Invalid JSON in package.json

**Fix:**
```bash
# Validate the file
node -e "JSON.parse(require('fs').readFileSync('package.json', 'utf8'))"

# If error, look at the file
cat package.json

# Look for:
# - Merge conflict markers
# - Duplicate keys
# - Missing commas
# - Branch names

# Replace with clean version from this guide
```

---

### Error: "Merge conflict in package.json"

**Cause:** Two branches modified the same lines

**Fix:**
```bash
# Option 1: Use theirs (incoming changes)
git checkout --theirs package.json
git add package.json
git commit

# Option 2: Use ours (keep current)
git checkout --ours package.json
git add package.json
git commit

# Option 3: Merge manually
# Edit package.json, remove markers, validate, commit
```

---

### Error: "Duplicate key in JSON"

**Cause:** Merge conflict created duplicate entries

**Fix:**
```bash
# Find duplicates
cat package.json | grep '"name"'
# If you see multiple "name" entries, that's the problem

# Remove duplicates manually
# Keep only one version of each key
```

---

## 📋 Checklist: Safe Merging

Before merging any PR:

- [ ] CI/CD pipeline is green ✅
- [ ] JSON validation passed ✅
- [ ] No merge conflict markers ✅
- [ ] Build succeeds locally ✅
- [ ] Tests pass ✅
- [ ] Lint passes ✅
- [ ] No duplicate keys ✅
- [ ] No branch names in files ✅

---

## 🎓 Learning Points

### Why This Happened

1. **Multiple PRs modified package.json** from the same base branch
2. **Changes weren't sequentially merged** - all created in parallel
3. **Merge conflict resolution was incomplete** or automated
4. **CI didn't catch it** because validation wasn't in place

### How We Fixed It

1. ✅ **Replaced corrupted package.json** with clean version
2. ✅ **Added GitHub Actions** to validate on every PR
3. ✅ **Added git hooks** to validate before commits
4. ✅ **Created validation script** for manual checking
5. ✅ **Updated workflow** to prevent future occurrences

### How to Prevent It

1. ✅ **Merge PRs sequentially** instead of in parallel
2. ✅ **Rebase frequently** to stay synced with main
3. ✅ **Run validation tools** before committing
4. ✅ **Use small, focused PRs** that are easier to merge
5. ✅ **Review CI logs** before merging

---

## 🚀 Going Forward

### Workflow for New Features

```bash
# 1. Sync with main
git checkout main
git pull origin main

# 2. Create feature branch
git checkout -b feature/new-feature

# 3. Make changes
# ... edit files ...

# 4. Validate before committing (automatic with husky)
git add .
git commit -m "feat: new feature"  # Pre-commit hook runs automatically

# 5. Push
git push origin feature/new-feature

# 6. Create PR
# GitHub Actions will validate automatically

# 7. Wait for CI to pass before merging
# 8. Merge via GitHub UI or:
git checkout main
git merge feature/new-feature
git push origin main

# 9. Delete feature branch
git branch -d feature/new-feature
git push origin --delete feature/new-feature
```

---

## ✅ Current Status

### Fixed Issues
- ✅ package.json is now valid JSON
- ✅ CI/CD pipeline will pass
- ✅ GitHub Actions validate on every PR
- ✅ Git hooks validate before every commit
- ✅ Manual validation script available

### Prevention Systems Active
- ✅ **2 GitHub Actions** (validate-json, merge-conflict-check)
- ✅ **1 Git hook** (pre-commit)
- ✅ **1 Validation script** (validate-json.sh)
- ✅ **Updated documentation** (this guide)

### Next PR Will Be Safe
- ✅ Automatic validation before merge
- ✅ CI catches issues immediately
- ✅ Can't commit invalid JSON
- ✅ Can't merge with conflicts

---

## 💡 Summary

**Problem**: Multiple PRs modified `package.json` in parallel, causing merge conflicts that weren't properly resolved.

**Solution**: 
1. Fixed the corrupted file
2. Added 4 layers of validation
3. Updated workflow practices
4. Documented prevention strategies

**Result**: This problem **cannot happen again** because:
- Git hooks block invalid commits locally
- GitHub Actions block invalid PRs remotely
- Validation runs automatically on every change
- Clear documentation prevents mistakes

---

**Your repository is now protected against JSON corruption! 🛡️**
