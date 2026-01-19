# Production Workflows Setup Guide

## 🚀 Overview

You now have **4 production-ready GitHub workflows** integrated with your Alibaba Cloud Security Analyzer:

1. **Authority Engine** - Notion to WordPress content pipeline
2. **Tax Collector** - Guardian humanitarian crisis detection
3. **Kaggle Intelligence** - Weekly data pipeline and predictive analytics
4. **Security Monitoring** - Hourly security compliance checks

## 📜 Workflow Details

### 1. Authority Engine (`authority-engine.yml`)

**Purpose:** Automated content creation and distribution pipeline

**Schedule:** Daily at 6 AM SAST (4 AM UTC)

**Workflow:**
```
Notion Content → Judge Verification → BRIA Visuals → CData Enrichment → WordPress Publish → Social Distribution (Ayrshare) → Email (MailChimp) → Ads (Google + Brave)
```

**Manual Trigger:**
```bash
gh workflow run authority-engine.yml -f notion_page_id=YOUR_PAGE_ID
```

**Key Features:**
- ✅ Multi-LLM judge consensus verification
- ✅ Automated visual generation
- ✅ WordPress publishing with paywall support
- ✅ Multi-channel distribution
- ✅ Grafana & Asana integration
- ✅ Alibaba Security Analyzer logging

---

### 2. Tax Collector (`tax-collector.yml`)

**Purpose:** Real-time humanitarian crisis detection and response

**Schedule:** Every 6 hours

**Workflow:**
```
GDELT Monitoring → NewsAPI Validation → Judge Consensus → Guardian Article Generation → WordPress Publish → Revenue Tracking → Crypto Aid Deployment
```

**Severity Threshold:** 75+ (0-100 scale)

**Key Features:**
- ✅ Real-time GDELT event monitoring
- ✅ Multi-source validation (NewsAPI)
- ✅ AI consensus verification (threshold: 0.8)
- ✅ Automatic Guardian article publication
- ✅ 100% revenue → humanitarian aid (crypto)
- ✅ PayPal, Luno, Stellar integration

---

### 3. Kaggle Intelligence (`kaggle-intelligence.yml`)

**Purpose:** Weekly African trade data processing and forecasting

**Schedule:** Monday at midnight SAST (Sunday 22:00 UTC)

**Workflow:**
```
Kaggle Download → Data Processing → Databricks Upload → ML Predictions → Report Generation → BRIA Visualizations → Premium WordPress Publish
```

**Datasets:**
- World Bank Development Indicators
- UN Global Commodity Trade Statistics

**Key Features:**
- ✅ Automated Kaggle dataset downloads
- ✅ Databricks integration for big data processing
- ✅ Predictive analytics (Q1 2026 forecasts)
- ✅ Premium content with paywall ($500)
- ✅ BRIA data visualizations

---

### 4. Security Monitoring (`security-monitoring.yml`)

**Purpose:** Continuous security compliance monitoring

**Schedule:** Hourly

**Workflow:**
```
Alibaba Security Analyzer Query → Finding Classification → Alert Routing → Grafana Dashboard → Datadog Metrics → Asana Tasks
```

**Alert Thresholds:**
- 🚨 **CRITICAL:** Immediate Asana task (due today)
- ⚠️ **HIGH:** Priority task (due tomorrow)
- 📄 **MEDIUM/LOW:** Logged to Grafana & Datadog

**Key Features:**
- ✅ Real-time security finding detection
- ✅ Automated alert routing
- ✅ Multi-platform monitoring (Grafana, Datadog)
- ✅ Security report artifacts (30-day retention)

---

## 🔐 Required GitHub Secrets

### 🚨 CRITICAL: Set Up These Secrets NOW

Go to: [Repository Settings → Secrets and Variables → Actions](https://github.com/deedk822-lang/The-lab-verse-monitoring-/settings/secrets/actions)

### Alibaba Cloud (Security Analyzer)
```
ALIBABA_ACCESS_KEY_ID
ALIBABA_ACCESS_KEY_SECRET
```
**How to get:** [Alibaba Cloud Console](https://ram.console.aliyun.com/manage/ak) → AccessKey Management

### Notion API
```
NOTION_API_KEY
```
**How to get:** [Notion Integrations](https://www.notion.so/my-integrations) → Create New Integration

### AI Models
```
MISTRAL_API_KEY
MISTRAL_AGENT_ID
GROQ_API_KEY
GEMINI_API_KEY
BRIA_API_KEY
```
**How to get:**
- Mistral: [console.mistral.ai](https://console.mistral.ai/api-keys/)
- Groq: [console.groq.com](https://console.groq.com/keys)
- Gemini: [aistudio.google.com](https://aistudio.google.com/app/apikey)
- BRIA: [platform.bria.ai](https://platform.bria.ai/)

### WordPress & Distribution
```
WORDPRESS_TOKEN
AYRSHARE_API_KEY
MAILCHIMP_API_KEY
GOOGLE_ADS_API_KEY
BRAVE_ADS_API_KEY
```
**How to get:**
- WordPress: [rankyak.africa/wp-admin](https://rankyak.africa/wp-admin) → Applications
- Ayrshare: [app.ayrshare.com](https://app.ayrshare.com/)
- MailChimp: [mailchimp.com/api-keys](https://mailchimp.com/api-keys)
- Google Ads: [ads.google.com/api](https://ads.google.com/api)
- Brave Ads: [ads.brave.com](https://ads.brave.com/)

### Monitoring & Tasks
```
GRAFANA_TOKEN
ASANA_TOKEN
ASANA_WORKSPACE_ID
DATADOG_API_KEY
```
**How to get:**
- Grafana: [dimakatsomoleli.grafana.net](https://dimakatsomoleli.grafana.net/) → API Keys
- Asana: [app.asana.com/0/my-apps](https://app.asana.com/0/my-apps) → Personal Access Token
- Asana Workspace: Check Asana URL (e.g., `/0/1234567890123/list`)
- Datadog: [app.datadoghq.com/api-keys](https://app.datadoghq.com/api-keys)

### Data & Analytics
```
DATABRICKS_HOST
DATABRICKS_TOKEN
KAGGLE_JSON
CDATA_LICENSE
```
**How to get:**
- Databricks: Your Databricks workspace URL + Personal Access Token
- Kaggle: [kaggle.com/settings](https://kaggle.com/settings) → Create New API Token
- CData: Your CData Connect license key

### News & Events
```
NEWS_API_KEY
GDELT_API_KEY
```
**How to get:**
- NewsAPI: [newsapi.org/register](https://newsapi.org/register)
- GDELT: [blog.gdeltproject.org/gdelt-doc-2-0-api-debuts](https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/)

### Payment & Crypto
```
PAYPAL_CLIENT_ID
LUNO_API_KEY
STELLAR_SECRET
```
**How to get:**
- PayPal: [developer.paypal.com](https://developer.paypal.com/) → Dashboard
- Luno: [luno.com/wallet/security/api_keys](https://www.luno.com/wallet/security/api_keys)
- Stellar: Your Stellar wallet secret key

---

## ⚡ Quick Start

### 1. Set Up Secrets (REQUIRED)

```bash
# Use GitHub CLI to add secrets quickly
gh secret set ALIBABA_ACCESS_KEY_ID
gh secret set ALIBABA_ACCESS_KEY_SECRET
gh secret set NOTION_API_KEY
gh secret set ASANA_TOKEN
# ... repeat for all secrets above
```

### 2. Trigger First Workflow

```bash
# Test Authority Engine with manual trigger
gh workflow run authority-engine.yml \
  -f notion_page_id=2b8af2b8d06b8150a5acfe7aa7d8f221

# Monitor execution
gh run watch
```

### 3. View Workflow Runs

```bash
# List recent runs
gh run list --limit 10

# View specific run
gh run view <run-id>

# Download artifacts
gh run download <run-id>
```

---

## 📊 Monitoring Dashboard

### Grafana Dashboards
- **URL:** [dimakatsomoleli.grafana.net](https://dimakatsomoleli.grafana.net/)
- **Annotations:** Real-time workflow events
- **Metrics:** Security findings, content publications, crisis detections

### Datadog Metrics
- `security.analyzer.critical_findings`
- `security.analyzer.high_findings`
- `security.analyzer.total_findings`

### Asana Project
- **Workspace:** Dima Katsomoleli workspace
- **Auto-created tasks:** Critical alerts, publications, weekly reports

---

## 🛠️ Troubleshooting

### Workflow Not Running?

1. **Check secrets:** All required secrets must be set
2. **Check permissions:** Actions must be enabled in repo settings
3. **Check logs:** `gh run view <run-id> --log`

### Common Issues

**"Missing ALIBABA_ACCESS_KEY_ID"**
```bash
gh secret set ALIBABA_ACCESS_KEY_ID
# Paste your Alibaba access key ID
```

**"Notion API authentication failed"**
- Verify your Notion integration has access to the page
- Check that the page ID is correct (32-char hex string)

**"Kaggle 401 Unauthorized"**
- Recreate your kaggle.json file from [kaggle.com/settings](https://kaggle.com/settings)
- Set the entire JSON content as `KAGGLE_JSON` secret

**"Asana workspace not found"**
- Get your workspace ID from Asana URL
- Should be a long numeric string (e.g., `1234567890123`)

---

## 🔄 Workflow Schedules

| Workflow | Frequency | Next Run |
|----------|-----------|----------|
| Authority Engine | Daily 6 AM SAST | Check Actions tab |
| Tax Collector | Every 6 hours | Check Actions tab |
| Kaggle Intelligence | Monday midnight | Check Actions tab |
| Security Monitoring | Hourly | Check Actions tab |

---

## 📝 Workflow Logs

### Access Logs
```bash
# View latest run
gh run list --workflow=authority-engine.yml --limit 1
gh run view --log

# Download security reports
gh run download --name security-report-*
```

### Log Locations
- **GitHub Actions:** Repository → Actions tab
- **Grafana:** Annotations on dashboards
- **Datadog:** Metrics & events
- **Asana:** Task descriptions & comments

---

## 🚀 Next Steps

1. ✅ **Set up all secrets** (see list above)
2. ✅ **Test Authority Engine** with manual trigger
3. ✅ **Verify Grafana integration** (check annotations)
4. ✅ **Monitor Asana** for auto-created tasks
5. ✅ **Review Security Monitoring** (runs hourly)

---

## 📞 Support

**Workflow Issues:**
- Check GitHub Actions logs
- Review workflow YAML syntax
- Verify all secrets are set correctly

**API Issues:**
- Check API key validity
- Verify rate limits
- Review API documentation

**Integration Issues:**
- Test each service independently
- Check network connectivity
- Verify webhook endpoints

---

## 📚 Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Alibaba Cloud Security Analyzer](https://www.alibabacloud.com/help/en/access-analyzer)
- [Notion API Reference](https://developers.notion.com/)
- [Asana API Documentation](https://developers.asana.com/docs)
- [Grafana API Documentation](https://grafana.com/docs/grafana/latest/http_api/)

---

**Generated:** 2025-11-28
**Repository:** [The-lab-verse-monitoring-](https://github.com/deedk822-lang/The-lab-verse-monitoring-)
**Status:** ✅ Production Ready
