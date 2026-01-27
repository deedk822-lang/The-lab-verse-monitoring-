# 🛡️ VAAL AI Empire - Credit Protection System

**Enterprise-grade cost protection for multi-provider LLM deployments on Alibaba Cloud**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Security: Bandit](https://img.shields.io/badge/security-bandit-yellow.svg)](https://github.com/PyCQA/bandit)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Usage Tiers](#usage-tiers)
- [Security Features](#security-features)
- [Monitoring](#monitoring)
- [API Integration](#api-integration)
- [Troubleshooting](#troubleshooting)
- [Advanced Configuration](#advanced-configuration)

## 🎯 Overview

The **VAAL AI Empire Credit Protection System** prevents runaway costs on cloud instances by implementing multi-layer safeguards for LLM API usage. Perfect for:

- 💰 **Free tier Alibaba Cloud** instances
- 🤖 **Kimi CLI** automated code generation
- 🤗 **HuggingFace** model deployments
- 🔄 **Multi-provider** LLM systems

### The Problem

Uncontrolled LLM usage can lead to:
- ❌ Unexpected bills ($100s-$1000s per day)
- ❌ Service disruptions from quota exhaustion
- ❌ Resource overload on free tier instances
- ❌ No visibility into usage patterns

### The Solution

Our credit protection system provides:
- ✅ **Real-time quota tracking** (requests, tokens, cost)
- ✅ **Automatic circuit breakers** (stops runaway usage)
- ✅ **Multi-tier limits** (FREE, ECONOMY, STANDARD, PREMIUM)
- ✅ **Proactive alerts** (email + webhooks)
- ✅ **Resource monitoring** (CPU/Memory/Disk)
- ✅ **Comprehensive logging** (audit trail)

## ✨ Features

### 🔒 Protection Layers

#### 1. **Quota Management**
- Daily request limits
- Daily token limits
- Daily cost limits (USD)
- Hourly burst protection
- Per-request size limits

#### 2. **Circuit Breaker**
- Automatic activation at 95% usage
- Configurable duration
- Manual trigger capability
- Graceful request blocking

#### 3. **Resource Monitoring**
- CPU usage tracking
- Memory usage tracking
- Disk usage tracking
- Automatic throttling

#### 4. **Alert System**
- 📧 Email alerts (SMTP)
- 🔔 Webhook alerts (Slack/Discord)
- ⚠️ Warning at 70% usage
- 🚨 Critical at 90% usage

### 🛠️ Technical Features

- **FastAPI Middleware**: Automatic request interception
- **Async Background Service**: Non-blocking monitoring
- **Persistent Storage**: JSON-based usage tracking
- **Provider Agnostic**: Works with any LLM API
- **Zero Configuration**: Sensible defaults
- **Production Ready**: Systemd integration

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Client Application                        │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│               FastAPI Application                            │
│  ┌────────────────────────────────────────────────────┐     │
│  │    CreditProtectionMiddleware                       │     │
│  │  • Intercepts all LLM requests                      │     │
│  │  • Checks quotas                                    │     │
│  │  • Records usage                                    │     │
│  │  • Returns 429 if limit exceeded                    │     │
│  └────────────────────────────────────────────────────┘     │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│           CreditProtectionManager                            │
│  • Quota tracking (daily/hourly)                             │
│  • Circuit breaker logic                                     │
│  • Usage logging                                             │
│  • Persistent storage                                        │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│         CreditMonitorService (Background)                    │
│  • Hourly reset task                                         │
│  • Daily reset task                                          │
│  • Usage monitoring task                                     │
│  • Alert generation                                          │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Ubuntu 20.04+ or Alibaba Cloud ECS
- Python 3.10+
- PostgreSQL 15+ (optional)
- Redis 7+ (optional)
- 2GB+ RAM

### One-Command Installation

```bash
# Clone repository
git clone https://github.com/deedk822-lang/The-lab-verse-monitoring-.git
cd The-lab-verse-monitoring-

# Run automated setup (requires sudo)
sudo ./scripts/setup-alibaba-cloud-protection.sh
```

This script will:
1. Install system dependencies
2. Set up Python environment
3. Configure directories
4. Create systemd service
5. Set up log rotation
6. Install health check

### Manual Installation

```bash
# 1. Create directories
mkdir -p /var/lib/vaal/credit_protection
mkdir -p /var/log/vaal

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
nano .env  # Edit with your values

# 4. Generate secrets
openssl rand -hex 32  # SECRET_KEY
openssl rand -hex 32  # JWT_SECRET_KEY

# 5. Start service
python -m vaal_ai_empire.credit_protection.monitor_service
```

## ⚙️ Configuration

### Environment Variables

Edit `/etc/vaal/.env` (or `.env` in project root):

```bash
# ============================================================================
# CRITICAL SETTINGS
# ============================================================================

# Credit tier (FREE, ECONOMY, STANDARD, PREMIUM)
CREDIT_TIER=free

# HuggingFace token (REQUIRED for model downloads)
HF_TOKEN=your_huggingface_token_here

# LLM provider selection
LLM_PROVIDER=huggingface

# Storage path
CREDIT_PROTECTION_PATH=/var/lib/vaal/credit_protection

# ============================================================================
# OPTIONAL: ALERTS
# ============================================================================

# Email alerts
ALERT_EMAIL_ENABLED=true
ALERT_EMAIL_TO=your-email@example.com
ALERT_EMAIL_FROM=vaal-alerts@yourdomain.com
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-gmail@gmail.com
SMTP_PASSWORD=your-app-password

# Webhook alerts (Slack/Discord)
ALERT_WEBHOOK_ENABLED=true
ALERT_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# ============================================================================
# OPTIONAL: RESOURCE LIMITS
# ============================================================================

MAX_CPU_PERCENT=80
MAX_MEMORY_PERCENT=85
MAX_DISK_PERCENT=90
```

### Get HuggingFace Token

1. Visit [https://huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)
2. Click "New token"
3. Select "Read" access
4. Copy token and set as `HF_TOKEN`

### Configure Gmail for Alerts

1. Enable 2FA on your Google account
2. Generate App Password: [https://myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
3. Use the 16-character password (no spaces) as `SMTP_PASSWORD`

## 💎 Usage Tiers

### FREE Tier (Default)
**Perfect for development and personal projects**

- **Daily Limits:**
  - 50 requests/day
  - 25,000 tokens/day
  - $0.25/day max cost
- **Hourly Limits:**
  - 10 requests/hour
  - 5,000 tokens/hour
  - $0.05/hour
- **Per-Request:**
  - 2,000 max tokens
  - $0.02 max cost

### ECONOMY Tier
**For small teams and prototypes**

- **Daily Limits:**
  - 100 requests/day
  - 50,000 tokens/day
  - $0.50/day
- **Hourly Limits:**
  - 20 requests/hour
  - 10,000 tokens/hour
  - $0.10/hour
- **Per-Request:**
  - 4,000 max tokens
  - $0.05 max cost

### STANDARD Tier
**For production applications**

- **Daily Limits:**
  - 300 requests/day
  - 150,000 tokens/day
  - $2.00/day
- **Hourly Limits:**
  - 50 requests/hour
  - 30,000 tokens/hour
  - $0.35/hour
- **Per-Request:**
  - 8,000 max tokens
  - $0.15 max cost

### PREMIUM Tier
**For high-volume enterprise use**

- **Daily Limits:**
  - 500 requests/day
  - 300,000 tokens/day
  - $5.00/day
- **Hourly Limits:**
  - 100 requests/hour
  - 60,000 tokens/hour
  - $0.75/hour
- **Per-Request:**
  - 16,000 max tokens
  - $0.30 max cost

## 🔐 Security Features

### Input Sanitization

```python
from vaal_ai_empire.api.sanitizers import sanitize_prompt

# Automatically blocks prompt injection attempts
user_input = sanitize_prompt(request.prompt, max_length=10000)
```

**Protects against:**
- Prompt injection attacks
- System prompt override attempts
- Code execution via prompts
- Null byte injection

### SSRF Protection

```python
from vaal_ai_empire.api.secure_requests import create_ssrf_safe_async_session

# Safe HTTP client that blocks private IPs
async with create_ssrf_safe_async_session() as client:
    response = await client.get(url)
```

**Blocks access to:**
- Private IP ranges (10.0.0.0/8, 192.168.0.0/16, etc.)
- Localhost (127.0.0.1, ::1)
- Link-local addresses (169.254.0.0/16)
- Cloud metadata APIs

## 📊 Monitoring

### Live Dashboard

```bash
./scripts/dashboard.sh
```

**Displays:**
- Real-time usage statistics
- Progress bars for quotas
- Circuit breaker status
- System resource usage
- Auto-refreshes every 5 seconds

### Health Check

```bash
/usr/local/bin/vaal-health-check
```

**Returns:**
- Current tier
- Usage statistics
- Circuit breaker status
- Exit code 0 (healthy) or 1 (unhealthy)

### Systemd Service Status

```bash
# Check service status
systemctl status vaal-credit-protection

# View live logs
journalctl -u vaal-credit-protection -f

# Restart service
sudo systemctl restart vaal-credit-protection
```

### Usage Logs

All requests are logged to:
```
/var/lib/vaal/credit_protection/usage_log_YYYY-MM.jsonl
```

Each line contains:
```json
{
  "timestamp": "2026-01-27T08:30:15.123456",
  "provider": "huggingface",
  "request_tokens": 150,
  "response_tokens": 850,
  "total_tokens": 1000,
  "estimated_cost": 0.01,
  "duration_ms": 2340,
  "status": "success",
  "metadata": {
    "endpoint": "/api/generate",
    "method": "POST"
  }
}
```

## 🔌 API Integration

### FastAPI Middleware

```python
from fastapi import FastAPI
from vaal_ai_empire.credit_protection.middleware import CreditProtectionMiddleware

app = FastAPI()

# Add credit protection middleware
app.add_middleware(
    CreditProtectionMiddleware,
    enable_resource_monitoring=True
)

@app.post("/api/generate")
async def generate(request: GenerateRequest):
    # Middleware automatically:
    # 1. Checks quota before processing
    # 2. Records usage after completion
    # 3. Returns 429 if limit exceeded
    return await llm_provider.generate(request.prompt)
```

### Manual Usage Tracking

```python
from vaal_ai_empire.credit_protection.manager import get_manager, ProviderType

manager = get_manager()

# Check if request is allowed
allowed, reason = manager.check_quota(
    estimated_tokens=2000,
    estimated_cost=0.02
)

if not allowed:
    raise HTTPException(status_code=429, detail=reason)

# Process request...
response = await llm_provider.generate(prompt)

# Record actual usage
manager.record_usage(
    provider=ProviderType.HUGGINGFACE,
    request_tokens=150,
    response_tokens=850,
    cost=0.01,
    duration_ms=2340,
    status="success"
)
```

### Response Headers

All LLM API responses include usage headers:

```http
HTTP/1.1 200 OK
X-Daily-Requests-Used: 15
X-Daily-Tokens-Used: 12500
X-Daily-Cost-Used: $0.1250
X-RateLimit-Limit: 50
X-RateLimit-Remaining: 35
X-RateLimit-Reset: 2026-01-28T00:00:00Z
```

### 429 Response (Quota Exceeded)

```json
{
  "error": "Credit limit exceeded",
  "reason": "Daily request limit reached (50)",
  "usage": {
    "tier": "free",
    "daily": {
      "requests": 50,
      "tokens": 25000,
      "cost_usd": 0.25,
      "usage_percent": {
        "requests": 100,
        "tokens": 100,
        "cost": 100
      }
    }
  },
  "retry_after": 43200
}
```

## 🚨 Emergency Shutdown

If you detect unusual usage patterns:

```bash
sudo ./scripts/emergency-shutdown.sh
```

**This will:**
1. Activate circuit breaker for 24 hours
2. Stop credit protection service
3. Stop API server
4. Block all new LLM requests

**To resume:**
```bash
# 1. Investigate issue
tail -f /var/log/vaal/credit-protection.log

# 2. Reset circuit breaker
python3 <<EOF
from vaal_ai_empire.credit_protection.manager import get_manager
manager = get_manager()
manager.circuit_open = False
manager._save_usage()
EOF

# 3. Restart services
sudo systemctl start vaal-credit-protection
```

## 🔧 Troubleshooting

### Circuit Breaker Stuck Open

**Symptoms:** All requests return 429 even after quota reset

**Solution:**
```bash
python3 <<EOF
from vaal_ai_empire.credit_protection.manager import get_manager
manager = get_manager()
manager.circuit_open = False
manager.circuit_open_until = None
manager._save_usage()
print("Circuit breaker reset")
EOF
```

### Incorrect Usage Tracking

**Symptoms:** Usage shows incorrect values

**Solution:**
```bash
# Reset daily usage
python3 <<EOF
from vaal_ai_empire.credit_protection.manager import get_manager
manager = get_manager()
manager.reset_daily_usage()
print("Daily usage reset")
EOF
```

### Service Won't Start

**Check logs:**
```bash
journalctl -u vaal-credit-protection -n 50
```

**Common issues:**
1. Missing `.env` file
2. Invalid HF_TOKEN
3. Permission issues on `/var/lib/vaal`
4. PostgreSQL/Redis not running

**Fix permissions:**
```bash
sudo chown -R vaal:vaal /var/lib/vaal /var/log/vaal
sudo chmod 755 /var/lib/vaal /var/log/vaal
```

## 📚 Advanced Configuration

### Custom Quotas

```python
from vaal_ai_empire.credit_protection.manager import (
    CreditProtectionManager,
    UsageQuota,
    TierLevel
)

# Define custom quota
custom_quota = UsageQuota(
    daily_requests=200,
    daily_tokens=100000,
    daily_cost_usd=1.00,
    hourly_requests=30,
    hourly_tokens=15000,
    hourly_cost_usd=0.15,
    max_request_tokens=5000,
    max_response_tokens=3000,
    max_request_cost_usd=0.08
)

manager = CreditProtectionManager(
    quota=custom_quota,
    tier=TierLevel.CUSTOM,
    storage_path="/var/lib/vaal/credit_protection"
)
```

### Alert Customization

```python
from vaal_ai_empire.credit_protection.monitor_service import CreditMonitorService

service = CreditMonitorService()

# Change alert thresholds
service.warning_threshold = 60  # Alert at 60%
service.critical_threshold = 85  # Critical at 85%

# Custom alert logic
async def custom_alert_handler(usage: dict):
    if usage['daily']['usage_percent']['cost'] > 80:
        # Your custom logic
        await send_to_pagerduty(usage)

service._send_critical_alert = custom_alert_handler
```

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## 📄 License

MIT License - see [LICENSE](LICENSE) file

## 🆘 Support

- **Issues:** [GitHub Issues](https://github.com/deedk822-lang/The-lab-verse-monitoring-/issues)
- **Discussions:** [GitHub Discussions](https://github.com/deedk822-lang/The-lab-verse-monitoring-/discussions)
- **Email:** deedk822@gmail.com

## 🙏 Acknowledgments

- Alibaba Cloud for free tier hosting
- HuggingFace for model hosting
- Kimi CLI for code generation
- FastAPI team for excellent framework

---

**Made with ❤️ for the open-source community**
