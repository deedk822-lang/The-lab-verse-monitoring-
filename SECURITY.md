# Security Policy

## Workflow Security Configuration

This document outlines the required GitHub Actions secrets and security best practices for running workflows in this repository.

## Required GitHub Secrets

All workflows use GitHub Actions secrets to protect sensitive credentials. Configure these in:
**Settings → Secrets and variables → Actions → New repository secret**

### Core API Keys

| Secret Name | Description | Used In |
|-------------|-------------|---------|
| `NOTION_API_KEY` | Notion integration token | Authority Engine, G20 Workflow |
| `MISTRAL_API_KEY` | Mistral AI API key | Judge System, Content Generation |
| `GROQ_API_KEY` | Groq API key | Judge System Verification |
| `GEMINI_API_KEY` | Google Gemini API key | Judge System Verification |
| `BRIA_API_KEY` | BRIA AI visual generation | Image Generation |
| `HF_API_TOKEN` | HuggingFace API token | Model Inference |
| `DEEP_INFRA_API_KEY` | Deep Infra API key | Model Hosting |

### Cloud Infrastructure

| Secret Name | Description | Used In |
|-------------|-------------|---------|
| `ALIBABA_ACCESS_KEY_ID` | Alibaba Cloud access key | Security Analyzer |
| `ALIBABA_ACCESS_KEY_SECRET` | Alibaba Cloud secret key | Security Analyzer |
| `ALIBABA_REGION` | Alibaba Cloud region (e.g., cn-shanghai) | Cloud Services |
| `AWS_ANALYZER_ARN` | AWS Security Analyzer ARN | Security Logging |
| `VERCEL_TOKEN` | Vercel deployment token | Gateway Deployment |

### Data & Analytics

| Secret Name | Description | Used In |
|-------------|-------------|---------|
| `CDATA_LICENSE` | CData connectivity license | Data Integration |
| `DATABRICKS_TOKEN` | Databricks workspace token | Data Processing |
| `KAGGLE_USERNAME` | Kaggle username | Dataset Management |
| `KAGGLE_KEY` | Kaggle API key | Dataset Management |

### Marketing & Distribution

| Secret Name | Description | Used In |
|-------------|-------------|---------|
| `AYRSHARE_API_KEY` | Ayrshare social media API | Social Distribution |
| `MAILCHIMP_API_KEY` | MailChimp campaign API | Email Marketing |
| `GOOGLE_ADS_API_KEY` | Google Ads API key | Ad Campaigns |
| `BRAVE_ADS_API_KEY` | Brave Ads API key | Ad Campaigns |
| `WORDPRESS_USERNAME` | WordPress.com username | Content Publishing |
| `WORDPRESS_PASSWORD` | WordPress.com app password | Content Publishing |

### Project Management

| Secret Name | Description | Used In |
|-------------|-------------|---------|
| `GRAFANA_TOKEN` | Grafana API token | Dashboard Updates |
| `ASANA_TOKEN` | Asana API token | Task Management |
| `ASANA_WORKSPACE_ID` | Asana workspace ID | Task Creation |
| `GITHUB_TOKEN` | GitHub PAT (auto-provided) | Repository Operations |

### Gateway Configuration

| Secret Name | Description | Used In |
|-------------|-------------|---------|
| `GATEWAY_API_KEY` | MCP Gateway API key | Gateway Authentication |
| `GATEWAY_URL` | Gateway URL (can be public var) | Gateway Endpoint |

## Security Best Practices

### 1. Never Hardcode Secrets

❌ **NEVER DO THIS:**
```yaml
env:
  API_KEY: "sk-1234567890abcdef"  # NEVER hardcode!
  REGION: "cn-shanghai"  # OK for non-sensitive config
```

✅ **ALWAYS DO THIS:**
```yaml
env:
  API_KEY: ${{ secrets.API_KEY }}
  REGION: ${{ secrets.REGION || 'cn-shanghai' }}  # Default fallback OK
```

### 2. Sensitive vs Non-Sensitive Data

**Sensitive (Use Secrets):**
- API keys, tokens, passwords
- Cloud credentials (access keys, ARNs with account IDs)
- Database connection strings
- Private endpoints with authentication

**Non-Sensitive (Can be in code):**
- Public API endpoints
- Region names (without credentials)
- Timeout values, retry counts
- Feature flags

### 3. Secret Rotation

- Rotate API keys every 90 days
- Immediately rotate if:
  - Key appears in logs
  - Team member leaves
  - Suspected compromise
- Use GitHub's secret scanning alerts

### 4. Workflow Permissions

```yaml
permissions:
  contents: read
  issues: write
  pull-requests: write
```

Only grant minimum necessary permissions.

### 5. Audit Trail

All workflow runs are logged:
- View in Actions tab
- Monitor for unauthorized access
- Review failed authentications

## Reporting Security Issues

If you discover a security vulnerability:

1. **DO NOT** create a public issue
2. Email: [your-security-email]
3. Include:
   - Description of vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

## Secret Verification Script

Run this locally to verify your secrets setup:

```bash
#!/bin/bash
# verify-secrets.sh

echo "🔍 Checking for hardcoded secrets..."

# Check for potential API keys
grep -r -E "(api[_-]?key|secret|token|password).*=.*['\"].*['\"]" .github/workflows/ && \
  echo "⚠️  Found potential hardcoded secrets!" || \
  echo "✅ No hardcoded secrets found"

# Check for hardcoded URLs with tokens
grep -r -E "https?://[^\s]*\?.*token=" .github/workflows/ && \
  echo "⚠️  Found URLs with tokens!" || \
  echo "✅ No URLs with tokens found"

# Check for AWS ARNs
grep -r -E "arn:aws:[a-z]+:[a-z0-9-]+:[0-9]+:" .github/workflows/ && \
  echo "⚠️  Found hardcoded ARNs!" || \
  echo "✅ No hardcoded ARNs found"

echo ""
echo "🎯 Required Secrets Check:"
echo "Verify these are configured in GitHub Settings:"
echo "  - NOTION_API_KEY"
echo "  - MISTRAL_API_KEY"
echo "  - GROQ_API_KEY"
echo "  - GEMINI_API_KEY"
echo "  - BRIA_API_KEY"
echo "  - ALIBABA_ACCESS_KEY_ID"
echo "  - ALIBABA_ACCESS_KEY_SECRET"
echo "  - And all others listed above"
```

## Workflow-Specific Security Notes

### Authority Engine (`authority-engine.yml`)
- Uses judge system consensus (multi-API verification)
- Logs all publications to Security Analyzer
- Requires: Notion, Judge APIs, BRIA, Publishing APIs

### G20 Workflow (`G20_CONTENT_WORKFLOW.md`)
- Multi-platform content distribution
- Requires: All marketing and social media APIs
- Enhanced security logging for compliance

### Kaggle Intelligence (if exists)
- Dataset access only
- Requires: Kaggle credentials, AWS Analyzer
- Limited permissions scope

## Compliance & Regulations

- **GDPR**: User data handled per GDPR guidelines
- **Cloud Compliance**: Alibaba Cloud & AWS security standards
- **API Rate Limits**: Respects all provider rate limits
- **Data Retention**: Logs retained per policy

## Last Updated

November 29, 2025

## Version

1.0.0 - Initial security documentation
