# 🔒 Security Automation Scripts

Quick reference for security hardening scripts powered by Moonshot AI (Kimi).

---

## 📁 Files

| Script | Purpose |
|--------|---------|
| `secure_file.py` | Harden a single file |
| `bulk_harden.py` | Harden multiple files in parallel |
| `harden_pr.sh` | Harden changed files in PR |
| `generate_artifact.py` | Generate security artifacts |

---

## 🚀 Quick Start

### 1. Set API Key

```bash
export MOONSHOT_API_KEY="sk-your-api-key-here"
```

### 2. Harden a File

```bash
python3 secure_file.py docker-compose.yml
```

### 3. Bulk Harden Repository

```bash
# Dry run first
python3 bulk_harden.py /path/to/repo --dry-run

# Apply hardening
python3 bulk_harden.py /path/to/repo
```

### 4. Generate Security Artifacts

```bash
# List available artifacts
python3 generate_artifact.py --list

# Generate specific artifact
python3 generate_artifact.py trivy-scan

# Generate all artifacts
python3 generate_artifact.py --all
```

---

## 📖 Usage

### secure_file.py

Harden a single file using Moonshot AI.

```bash
# Basic usage (overwrites original)
python3 secure_file.py <file_path>

# Save to different file
python3 secure_file.py <input_file> <output_file>

# Examples
python3 secure_file.py config.py
python3 secure_file.py docker-compose.yml docker-compose.secure.yml
```

**Output:** JSON result with status, paths, and sizes.

### bulk_harden.py

Harden multiple files in parallel.

```bash
# Basic usage
python3 bulk_harden.py <repo_path>

# Options
python3 bulk_harden.py <repo_path> [OPTIONS]

Options:
  --output, -o DIR       Save hardened files to separate directory
  --workers, -w NUM      Number of parallel workers (default: 4)
  --dry-run, -n          Preview changes without modifying files
  --json                 Output results as JSON

# Examples
python3 bulk_harden.py .
python3 bulk_harden.py . --dry-run
python3 bulk_harden.py . --output ./hardened
python3 bulk_harden.py . --workers 8 --json
```

**Output:** Summary with success/failure counts and error details.

### harden_pr.sh

Harden changed files in current branch (for PRs).

```bash
# Basic usage
bash harden_pr.sh

# In CI environment (auto-commits)
CI=true bash harden_pr.sh
```

**Features:**
- Detects changed files automatically
- Filters security-critical files
- Hardens each file
- Commits changes in CI mode
- Shows summary

### generate_artifact.py

Generate security artifacts using Moonshot AI.

```bash
# List available artifacts
python3 generate_artifact.py --list

# Generate specific artifact
python3 generate_artifact.py <artifact_type>

# Generate all artifacts
python3 generate_artifact.py --all

# Options
python3 generate_artifact.py <artifact_type> [OPTIONS]

Options:
  --output, -o PATH      Custom output path
  --output-dir DIR       Output directory for all artifacts (with --all)
  --json                 Output results as JSON

# Examples
python3 generate_artifact.py trivy-scan
python3 generate_artifact.py secret-rotation --output ./custom/rotate.sh
python3 generate_artifact.py --all
python3 generate_artifact.py --all --output-dir ./security-artifacts
```

**Available artifacts:**
- `trivy-scan` - Trivy security scanning workflow
- `secret-rotation` - Secret rotation script
- `k8s-security` - Kubernetes security policies
- `docker-security` - Docker security configs
- `security-checklist` - Security checklist
- `dependabot` - Dependabot configuration
- `pre-commit` - Pre-commit hooks
- `security-policy` - Security policy document

---

## 🔧 Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `MOONSHOT_API_KEY` | Yes | Your Moonshot AI API key |

### File Patterns

**Hardened file types:**
- Python: `*.py`
- YAML: `*.yml`, `*.yaml`
- Docker: `Dockerfile*`
- Environment: `*.env.example`
- Shell: `*.sh`, `*.bash`
- JavaScript: `*.js`, `*.ts`
- Go: `*.go`
- Config: `*.conf`, `*.config`

**Excluded directories:**
- `.git`, `node_modules`, `__pycache__`
- `.venv`, `venv`, `dist`, `build`
- `.pytest_cache`, `.mypy_cache`

**Excluded files:**
- `.env` (actual secrets)
- Lock files (`package-lock.json`, etc.)

---

## 🛡️ Security Principles

All hardening follows OWASP best practices:

### Python
- Remove hardcoded credentials
- Add input validation
- Use parameterized queries
- Implement proper error handling
- Use secure random generation

### YAML/Docker Compose
- Remove hardcoded passwords
- Use Docker secrets
- Set resource limits
- Run as non-root
- Enable health checks

### Dockerfiles
- Use specific image versions
- Run as non-root user
- Multi-stage builds
- No secrets in layers
- Proper file permissions

### Shell Scripts
- Validate inputs
- Quote variables properly
- Use `set -euo pipefail`
- Avoid eval
- Implement timeouts

---

## 📊 Output Examples

### secure_file.py

```json
{
  "status": "success",
  "original_path": "config.py",
  "output_path": "config.py",
  "original_size": 1234,
  "hardened_size": 1567
}
```

### bulk_harden.py

```json
{
  "total_files": 42,
  "success": 40,
  "failed": 2,
  "errors": [
    {
      "file": "broken.py",
      "error": "API request failed: timeout"
    }
  ],
  "files": [...]
}
```

### generate_artifact.py

```json
{
  "status": "success",
  "artifact_type": "trivy-scan",
  "output_path": ".github/workflows/trivy-scan.yml",
  "size": 2048
}
```

---

## 🐛 Troubleshooting

### API Key Not Set

```bash
export MOONSHOT_API_KEY="sk-your-key-here"
```

### Permission Denied

```bash
chmod +w path/to/file
```

### Slow Processing

```bash
# Increase workers
python3 bulk_harden.py . --workers 16
```

### API Rate Limits

- Reduce number of workers
- Add delays between requests
- Check API quota

---

## 📚 Additional Resources

- [Full Documentation](../../docs/SECURITY_AUTOMATION.md)
- [Moonshot AI Docs](https://platform.moonshot.cn/docs)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)

---

**Powered by:** [Moonshot AI (Kimi)](https://www.moonshot.cn/)

