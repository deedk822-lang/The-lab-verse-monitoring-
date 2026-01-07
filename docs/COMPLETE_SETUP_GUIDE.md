# Complete Setup & Recovery Guide (Automated)

This guide explains how to run the prepared scripts to remove secrets, purge history, reorganize the repo, and add CI.

Important safety notes:
- Always rotate secrets BEFORE you purge history.
- Create backups before rewriting Git history.
- Communicate to collaborators when rewriting history; they must re-clone.

Quick commands (automated, recommended):
```bash
# 1. Save the scripts into repo root and make executable
chmod +x security-cleanup.sh purge-secrets-from-history.sh repo-cleanup.sh

# 2. Run security cleanup (dries-run first)
./security-cleanup.sh DRY_RUN=yes

# 3. If output looks good, run non-dry:
./security-cleanup.sh

# 4. Run gitleaks locally to verify:
gitleaks detect --source . --report-path gitleaks-report.json --no-git || true
cat gitleaks-report.json | jq '.'

# 5. If secrets were found and rotated, run purge (git-filter-repo recommended)
#    Edit /tmp/secrets-to-replace.txt with mappings (actual_secret==>[REDACTED])
./purge-secrets-from-history.sh REPLACE_FILE=/tmp/secrets-to-replace.txt

# 6. Re-run gitleaks; verify nothing sensitive remains
gitleaks detect --source . --report-path gitleaks-report-after.json --no-git || true

# 7. Run repo cleanup to fix filenames and structure (dry-run first)
./repo-cleanup.sh DRY_RUN=yes
# Then:
./repo-cleanup.sh

# 8. Push changes or open a PR; if history was rewritten, force-push required.
git push origin main
# If history rewritten:
git push origin --force --all
git push origin --force --tags
```

Follow the in-script prompts if you do not pass forced environment variables. See each script head for env variables available.

After force-pushing, instruct collaborators:
```bash
# collaborators should:
git clone https://github.com/<owner>/<repo>.git
```

For CI: commit `.github/workflows/ci-cd-pipeline.yml` (provided) and push; the workflow includes Gitleaks and CodeQL scans.

If you want me to open a PR with these files, provide:
- repo owner/name (example: owner/repo)
- branch name to target (default: main)
- permission to create a branch and open a PR (yes/no).
