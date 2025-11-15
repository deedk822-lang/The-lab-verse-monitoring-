# 🔒 Security Automation with Moonshot AI (Kimi)

Complete guide to automated security hardening using Moonshot AI API integration.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Features](#features)
- [Setup](#setup)
- [Usage](#usage)
  - [Single File Hardening](#single-file-hardening)
  - [Bulk Hardening](#bulk-hardening)
  - [PR Hardening](#pr-hardening)
  - [Artifact Generation](#artifact-generation)
- [CI/CD Integration](#cicd-integration)
- [Makefile Commands](#makefile-commands)
- [How It Works](#how-it-works)
- [Security Principles](#security-principles)
- [Troubleshooting](#troubleshooting)

---

## Overview

This repository includes **automated security hardening** powered by **Moonshot AI (Kimi)**. Instead of manually reviewing and fixing security issues, you can now:

- **Auto-harden** individual files or entire repositories
- **Bulk-process** security-critical files in parallel
- **Automate** security checks in CI/CD pipelines
- **Generate** missing security artifacts on demand

All hardening follows **OWASP best practices** and is context-aware based on file types.

---

## Quick Start

### 1. Set up API key

```bash
export MOONSHOT_API_KEY="sk-your-api-key-here"
```

### 2. Harden a single file

```bash
make secure FILE=docker-compose.yml
```

### 3. Harden all security-critical files

```bash
# Dry run first (recommended)
make secure-bulk-dry

# Apply hardening
make secure-bulk
```

### 4. Generate security artifacts

```bash
# Generate all security artifacts
make generate-all-artifacts

# Or generate specific artifact
make generate-artifact TYPE=trivy-scan
```

---

## Features

### ✅ Automated Security Hardening

- **Context-aware**: Different rules for Python, YAML, Dockerfiles, shell scripts, etc.
- **OWASP-compliant**: Follows industry best practices
- **Parallel processing**: Harden multiple files simultaneously
- **Dry-run mode**: Preview changes before applying

### 🔧 Security Artifact Generation

Generate missing security files:

- **Trivy scan workflows** (`.github/workflows/trivy-scan.yml`)
- **Secret rotation scripts** (`scripts/security/rotate-secrets.sh`)
- **Kubernetes security policies** (`k8s/security-policies.yaml`)
- **Docker security configs** (`.dockerignore`)
- **Security checklists** (`SECURITY_CHECKLIST.md`)
- **Dependabot configs** (`.github/dependabot.yml`)
- **Pre-commit hooks** (`.pre-commit-config.yaml`)
- **Security policies** (`SECURITY.md`)

### 🚀 CI/CD Integration

- **GitHub Actions workflows** for automatic PR hardening
- **Scheduled security audits** (weekly by default)
- **Automated PR creation** with hardened files
- **PR comments** with hardening summaries

---

## Setup

### Prerequisites

- Python 3.11+
- Moonshot AI API key
- Git repository

### Installation

1. **Clone this repository** (already done if you're reading this)

2. **Install Python dependencies**:

```bash
pip install requests
```

3. **Set API key**:

```bash
# Option 1: Environment variable (temporary)
export MOONSHOT_API_KEY="sk-your-key-here"

# Option 2: Add to .bashrc/.zshrc (permanent)
echo 'export MOONSHOT_API_KEY="sk-your-key-here"' >> ~/.bashrc
source ~/.bashrc

# Option 3: GitHub repository secret (for CI/CD)
# Go to: Settings → Secrets and variables → Actions → New repository secret
# Name: MOONSHOT_API_KEY
# Value: sk-your-key-here
```

4. **Verify setup**:

```bash
python3 scripts/security/secure_file.py --help
```

---

## Usage

### Single File Hardening

Harden a specific file using Moonshot AI:

```bash
# Using Makefile
make secure FILE=config.py

# Using script directly
python3 scripts/security/secure_file.py config.py

# Save to different file
python3 scripts/security/secure_file.py config.py config.secure.py
```

**What it does:**
- Removes hardcoded credentials
- Adds input validation
- Implements secure defaults
- Enhances error handling
- Applies file-type specific security rules

### Bulk Hardening

Harden all security-critical files in the repository:

```bash
# Dry run first (recommended)
make secure-bulk-dry

# Apply hardening (overwrites files)
make secure-bulk

# Save to separate directory
python3 scripts/security/bulk_harden.py . --output ./hardened

# Use more workers for faster processing
python3 scripts/security/bulk_harden.py . --workers 8
```

**Files targeted:**
- `*.py` - Python files
- `*.yml`, `*.yaml` - YAML configs
- `Dockerfile*` - Docker files
- `*.env.example` - Environment templates
- `*.sh`, `*.bash` - Shell scripts
- `*.js`, `*.ts` - JavaScript/TypeScript
- `*.go` - Go files
- `*.conf`, `*.config` - Configuration files

**Excluded:**
- `.env` files (actual secrets)
- `node_modules/`, `.git/`, etc.
- Lock files (`package-lock.json`, etc.)

### PR Hardening

Harden only changed files in your current branch:

```bash
# Using Makefile
make secure-pr

# Using script directly
bash scripts/security/harden_pr.sh
```

**Use cases:**
- Before creating a PR
- In CI/CD pipeline
- After making changes to security-critical files

### Artifact Generation

Generate missing security artifacts:

```bash
# List available artifacts
make list-artifacts

# Generate specific artifact
make generate-artifact TYPE=trivy-scan
make generate-artifact TYPE=secret-rotation
make generate-artifact TYPE=k8s-security

# Generate all artifacts
make generate-all-artifacts

# Custom output path
python3 scripts/security/generate_artifact.py trivy-scan --output ./custom/path.yml
```

**Available artifacts:**

| Type | Output File | Description |
|------|-------------|-------------|
| `trivy-scan` | `.github/workflows/trivy-scan.yml` | Trivy security scanning workflow |
| `secret-rotation` | `scripts/security/rotate-secrets.sh` | Secret rotation script |
| `k8s-security` | `k8s/security-policies.yaml` | Kubernetes security policies |
| `docker-security` | `.dockerignore` | Docker security ignore file |
| `security-checklist` | `SECURITY_CHECKLIST.md` | Security checklist |
| `dependabot` | `.github/dependabot.yml` | Dependabot config |
| `pre-commit` | `.pre-commit-config.yaml` | Pre-commit hooks |
| `security-policy` | `SECURITY.md` | Security policy document |

---

## CI/CD Integration

### GitHub Actions

Two workflows are included:

#### 1. **Security Hardening** (`.github/workflows/security-hardening.yml`)

Automatically hardens changed files in PRs.

**Triggers:**
- Pull requests to `main`, `master`, `develop`
- Manual workflow dispatch

**What it does:**
- Detects changed security-critical files
- Hardens them using Moonshot AI
- Commits changes back to the PR
- Posts summary comment on PR

**Setup:**
1. Add `MOONSHOT_API_KEY` to repository secrets
2. Workflow runs automatically on PRs

#### 2. **Security Audit** (`.github/workflows/security-audit.yml`)

Full repository security audit on a schedule.

**Triggers:**
- Weekly (Monday 9 AM UTC)
- Manual workflow dispatch

**What it does:**
- Scans entire repository
- Hardens all security-critical files
- Creates PR with changes
- Generates audit report

**Setup:**
1. Add `MOONSHOT_API_KEY` to repository secrets
2. Workflow runs automatically weekly

### Local CI Integration

For other CI systems (GitLab CI, Jenkins, etc.):

```bash
# In your CI pipeline
export MOONSHOT_API_KEY="${SECRET_MOONSHOT_KEY}"
bash scripts/security/harden_pr.sh
```

---

## Makefile Commands

Complete reference of security automation commands:

| Command | Description |
|---------|-------------|
| `make secure FILE=<path>` | Harden a single file |
| `make secure-bulk` | Harden all security-critical files |
| `make secure-bulk-dry` | Dry-run bulk hardening |
| `make secure-pr` | Harden changed files in current branch |
| `make generate-artifact TYPE=<type>` | Generate specific security artifact |
| `make generate-all-artifacts` | Generate all security artifacts |
| `make list-artifacts` | List available artifacts |
| `make security-setup` | Complete security setup (artifacts + dry-run) |

---

## How It Works

### Architecture

```
┌─────────────────┐
│  Your File      │
│  (insecure)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  secure_file.py │
│  - Reads file   │
│  - Builds prompt│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Moonshot AI    │
│  (Kimi API)     │
│  - Analyzes     │
│  - Hardens      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Hardened File  │
│  (secure)       │
└─────────────────┘
```

### Security Prompt Engineering

Each file type gets a **context-aware security prompt**:

**Python files:**
- Remove hardcoded credentials
- Add input validation
- Use parameterized queries
- Implement proper error handling
- Use secure random generation

**YAML/Docker Compose:**
- Remove hardcoded passwords
- Use Docker secrets
- Set resource limits
- Run as non-root
- Enable health checks

**Dockerfiles:**
- Use specific image versions
- Run as non-root user
- Multi-stage builds
- No secrets in layers
- Proper file permissions

**Shell scripts:**
- Validate inputs
- Quote variables
- Use `set -euo pipefail`
- Avoid eval
- Implement timeouts

### Parallel Processing

Bulk hardening uses **ThreadPoolExecutor** for parallel processing:

```python
with ThreadPoolExecutor(max_workers=8) as executor:
    futures = [executor.submit(harden_file, f) for f in files]
    results = [future.result() for future in as_completed(futures)]
```

---

## Security Principles

All hardening follows these principles:

### 🔐 **Secrets Management**
- Remove hardcoded credentials
- Use environment variables
- Suggest secret management tools

### ✅ **Input Validation**
- Validate all user inputs
- Sanitize data before use
- Implement whitelist validation

### 🛡️ **Secure Defaults**
- Fail securely by default
- Principle of least privilege
- Disable unnecessary features

### 🚨 **Error Handling**
- Don't expose sensitive info in errors
- Log errors securely
- Implement proper exception handling

### 🔒 **Defense in Depth**
- Multiple layers of security
- Network isolation
- Resource limits

---

## Troubleshooting

### API Key Issues

**Problem:** `MOONSHOT_API_KEY environment variable not set`

**Solution:**
```bash
export MOONSHOT_API_KEY="sk-your-key-here"
```

### API Request Failures

**Problem:** `API request failed: 401 Unauthorized`

**Solution:** Check that your API key is valid and has sufficient credits.

### File Not Found

**Problem:** `File not found: path/to/file`

**Solution:** Use relative or absolute paths. Ensure file exists.

### Permission Denied

**Problem:** `Permission denied` when writing files

**Solution:**
```bash
chmod +w path/to/file
# Or run with sudo (not recommended)
```

### Bulk Hardening Too Slow

**Problem:** Bulk hardening takes too long

**Solution:** Increase workers:
```bash
python3 scripts/security/bulk_harden.py . --workers 16
```

### CI/CD Workflow Not Running

**Problem:** GitHub Actions workflow doesn't trigger

**Solution:**
1. Check that `MOONSHOT_API_KEY` is set in repository secrets
2. Ensure workflow file is in `.github/workflows/`
3. Check workflow permissions in repository settings

---

## Examples

### Example 1: Harden Docker Compose

**Before:**
```yaml
services:
  db:
    image: postgres:latest
    environment:
      POSTGRES_PASSWORD: mysecretpassword
```

**After:**
```yaml
services:
  db:
    image: postgres:15.3-alpine
    environment:
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    user: postgres
    read_only: true
    security_opt:
      - no-new-privileges:true
    resources:
      limits:
        memory: 512M
        cpus: '0.5'
```

### Example 2: Harden Python Script

**Before:**
```python
import os
API_KEY = "sk-1234567890"
db_query = f"SELECT * FROM users WHERE id = {user_id}"
```

**After:**
```python
import os
from typing import Optional

API_KEY = os.getenv("API_KEY")
if not API_KEY:
    raise ValueError("API_KEY environment variable not set")

def get_user(user_id: int) -> Optional[dict]:
    """Get user by ID with input validation"""
    if not isinstance(user_id, int) or user_id < 0:
        raise ValueError("Invalid user_id")
    
    # Use parameterized query
    db_query = "SELECT * FROM users WHERE id = ?"
    return db.execute(db_query, (user_id,)).fetchone()
```

---

## Additional Resources

- [Moonshot AI Documentation](https://platform.moonshot.cn/docs)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Docker Security Best Practices](https://docs.docker.com/develop/security-best-practices/)
- [Kubernetes Security](https://kubernetes.io/docs/concepts/security/)

---

## Support

For issues or questions:

1. Check this documentation
2. Review error messages carefully
3. Check API key and permissions
4. Open an issue on GitHub

---

**Last Updated:** 2025-01-17

**Powered by:** [Moonshot AI (Kimi)](https://www.moonshot.cn/)

