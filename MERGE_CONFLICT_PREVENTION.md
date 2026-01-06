# 🛡️ Merge Conflict Prevention & Resolution Guide

## 🔍 What Happened

A `package.json` file became corrupted due to **unresolved merge conflicts** from multiple branches modifying the same file simultaneously. This resulted in:

- ❌ Invalid JSON syntax (duplicate keys, branch names embedded in file)
- ❌ CI/CD pipeline failures (`npm error EJSONPARSE`)
- ❌ Deployment blocked

---

## ✅ Prevention Systems Implemented

### 1. **GitHub Actions - Automatic Validation**

A GitHub Actions workflow (`.github/workflows/validate-json.yml`) runs on every PR and push to validate that all `.json` files have valid syntax. This prevents corrupted JSON from ever being merged into `main`.

### 2. **Branch Protection Rules**

The `main` branch is protected. All changes must come through a Pull Request, and all status checks (including the JSON validation) must pass before merging is allowed.

### 3. **Clear Communication**

When working on shared files like `package.json`, communicate with your team in the relevant Slack channel or PR to coordinate changes and avoid simultaneous updates.

---

## 🛠️ How to Resolve Conflicts

If you encounter a merge conflict, follow these steps:

### Step 1: Update Your Local Branch

First, ensure your local `main` branch is up-to-date, and then update your feature branch.

```bash
git checkout main
git pull origin main
git checkout your-feature-branch
git rebase main
```

### Step 2: Identify Conflicting Files

Git will list the files with conflicts. For example:

```
CONFLICT (content): Merge conflict in package.json
```

### Step 3: Resolve Manually

Open the conflicting file(s) in your editor. You will see conflict markers:

```json
{
  "name": "my-app",
<<<<<<< HEAD
  "version": "1.0.0",
=======
  "version": "2.0.0",
>>>>>>> feature-branch
}
```

- `<<<<<<< HEAD`: This is the start of the conflicting block from your current branch (HEAD).
- `=======`: This separates the two conflicting versions.
- `>>>>>>> feature-branch`: This is the end of the conflicting block from the branch you are merging.

To resolve the conflict, edit the file to remove the markers and choose which version of the code to keep. You might keep your version, the incoming version, or a combination of both.

**Example Resolution:**

```json
{
  "name": "my-app",
  "version": "2.0.0"
}
```

### Step 4: Stage and Commit the Fix

Once you have resolved all conflicts, stage the changes and continue the rebase or merge.

```bash
# After editing the file to fix conflicts
git add .
git rebase --continue
```

### Step 5: Push Your Changes

After the rebase is complete and all conflicts are resolved, force-push your changes to update the Pull Request.

```bash
git push --force-with-lease origin your-feature-branch
```
