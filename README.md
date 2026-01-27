# 🛡️ VAAL AI Empire - Credit Protection System

**Enterprise-grade cost protection for LLM deployments on Alibaba Cloud**

Prevents runaway costs on free-tier and pay-per-use cloud instances with multi-layer safeguards, real-time monitoring, and automatic circuit breakers.

---

## 🎯 Features

### 💰 **Multi-Tier Credit System**
- **FREE Tier**: 50 req/day, 25k tokens, $0.25/day
- **ECONOMY Tier**: 100 req/day, 50k tokens, $0.50/day  
- **STANDARD Tier**: 300 req/day, 150k tokens, $2.00/day
- **PREMIUM Tier**: 500 req/day, 300k tokens, $5.00/day

### 🔒 **Security & Protection**
- ✅ Prompt injection prevention
- ✅ SSRF-safe HTTP client
- ✅ Input sanitization & validation
- ✅ Multi-provider LLM abstraction

### 📊 **Real-Time Monitoring**
- ✅ Live usage dashboard
- ✅ Circuit breaker (auto-blocks at 95%)
- ✅ Email alerts (70% warning, 90% critical)
- ✅ Webhook alerts (Slack/Discord)
- ✅ Resource monitoring (CPU/RAM/Disk)
- ✅ Hourly burst protection

### 🚀 **LLM Provider Support**
- HuggingFace (with HF_TOKEN)
- OpenAI (GPT-3.5/4)
- Qwen/Alibaba DashScope
- Kimi AI CLI
- Z.AI (extensible)

---

## 📦 Installation

### **Quick Start (Automated)**

```bash
# Clone repository
git clone https://github.com/deedk822-lang/The-lab-verse-monitoring-.git
cd The-lab-verse-monitoring-

# Checkout the credit protection branch
git checkout security-hardening-llm-upgrade-222347293222010539

# Run automated setup
bash scripts/setup-alibaba-cloud-protection.sh
```

The script will:
1. ✅ Install system dependencies
2. ✅ Create Python virtual environment
3. ✅ Install Python packages
4. ✅ Configure `.env` file
5. ✅ Set up systemd service
6. ✅ Create storage directories
7. ✅ Verify installation

### **Manual Installation**

```bash
# 1. Install system dependencies
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv git curl jq bc

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 4. Create directories
sudo mkdir -p /var/lib/vaal/credit_protection
sudo mkdir -p /var/log/vaal
sudo chown -R $USER:$USER /var/lib/vaal /var/log/vaal

# 5. Configure environment
cp .env.example .env
nano .env  # Edit with your API keys
```

---

## ⚙️ Configuration

### **1. Environment Variables (.env)**

**CRITICAL - Required:**
```bash
# HuggingFace Token (REQUIRED for most models)
HF_TOKEN=hf_your_token_here  # Get from https://huggingface.co/settings/tokens

# Credit Protection Tier
CREDIT_TIER=free  # Options: free, economy, standard, premium

# LLM Provider
LLM_PROVIDER=huggingface  # Options: huggingface, openai, qwen
```

**Optional - Alerts:**
```bash
# Email Alerts
ALERT_EMAIL_ENABLED=true
ALERT_EMAIL_TO=your-email@example.com
SMTP_HOST=smtp.gmail.com
SMTP_USER=your-gmail@gmail.com
SMTP_PASSWORD=your-app-password  # Use Gmail App Password

# Webhook Alerts (Slack/Discord)
ALERT_WEBHOOK_ENABLED=true
ALERT_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

**Optional - Additional Providers:**
```bash
# OpenAI (if using GPT models)
OPENAI_API_KEY=sk-your_key_here

# Qwen/DashScope
QWEN_API_KEY=your_qwen_key_here

# Kimi AI
KIMI_API_KEY=your_kimi_key_here
```

### **2. Get HuggingFace Token**

1. Go to https://huggingface.co/settings/tokens
2. Click "New token"
3. Name: `vaal-ai-empire`
4. Type: **Read** (or **Write** for private models)
5. Copy token to `.env` file

### **3. Configure Gmail Alerts (Optional)**

1. Enable 2FA on Google Account
2. Generate App Password: https://myaccount.google.com/apppasswords
3. Use the 16-character password in `SMTP_PASSWORD`

---

## 🚀 Usage

### **Start the Service**

```bash
# Enable auto-start on boot
sudo systemctl enable credit-protection

# Start service
sudo systemctl start credit-protection

# Check status
sudo systemctl status credit-protection
```

### **Live Monitoring Dashboard**

```bash
./scripts/dashboard.sh
```

**Dashboard shows:**
- 📊 Real-time usage percentages
- 🔋 Daily/hourly quota consumption
- 💻 System resources (CPU/RAM/Disk)
- 🚨 Circuit breaker status
- 📈 Progress bars with color coding

### **Emergency Shutdown**

If you detect unusual activity or need to stop all LLM requests immediately:

```bash
./scripts/emergency-shutdown.sh
```

This will:
1. ⛔ Trigger circuit breaker (2 hours)
2. 🛑 Stop credit protection service
3. ❌ Kill all LLM processes
4. 🔒 Create emergency lockfile

### **View Logs**

```bash
# Live tail
tail -f /var/log/vaal/credit-protection.log

# Error logs
tail -f /var/log/vaal/credit-protection-error.log

# Usage history (monthly)
cat /var/lib/vaal/credit_protection/usage_log_2026-01.jsonl | jq
```

---

## 🔌 API Integration

### **FastAPI Middleware**

Add credit protection to your FastAPI app:

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
async def generate_text(prompt: str):
    # Your LLM logic here
    # Credit protection automatically enforced
    pass
```

### **Direct Usage in Code**

```python
from vaal_ai_empire.credit_protection import get_manager, ProviderType

manager = get_manager()

# Check quota before request
allowed, reason = manager.check_quota(
    estimated_tokens=4000,
    estimated_cost=0.04
)

if not allowed:
    print(f"Request blocked: {reason}")
    return

# Make LLM request
response = your_llm_function()

# Record usage
manager.record_usage(
    provider=ProviderType.HUGGINGFACE,
    request_tokens=2000,
    response_tokens=2000,
    cost=0.04,
    duration_ms=1500,
    status="success"
)
```

### **Get Usage Summary**

```python
from vaal_ai_empire.credit_protection import get_manager

manager = get_manager()
summary = manager.get_usage_summary()

print(f"Tier: {summary['tier']}")
print(f"Daily requests: {summary['daily']['requests']} / {summary['daily']['limits']['requests']}")
print(f"Daily cost: ${summary['daily']['cost_usd']:.4f}")
print(f"Circuit breaker: {summary['circuit_breaker']['open']}")
```

---

## 📊 Monitoring & Alerts

### **Alert Thresholds**

| Level | Threshold | Action |
|-------|-----------|--------|
| ⚠️ **Warning** | 70% | Email/Webhook alert |
| 🚨 **Critical** | 90% | Email/Webhook alert |
| ⛔ **Circuit Breaker** | 95% | Auto-block all requests |

### **Alert Channels**

**Email Example:**
```
Subject: ⚠️ Credit Usage Warning (70% threshold)

Your daily credit usage has reached the warning threshold.

Current Usage:
- Requests: 35 / 50 (70.0%)
- Tokens: 17,500 / 25,000 (70.0%)
- Cost: $0.175 / $0.25 (70.0%)

Tier: FREE
```

**Webhook Example (Slack/Discord):**
```json
{
  "text": "🚨 Credit Usage Warning",
  "attachments": [{
    "color": "#ffcc00",
    "text": "Daily usage: 70% of quota",
    "footer": "VAAL AI Empire Credit Protection"
  }]
}
```

---

## 🏗️ Architecture

```
vaal_ai_empire/
├── credit_protection/
│   ├── __init__.py          # Package exports
│   ├── manager.py           # Core quota manager
│   ├── middleware.py        # FastAPI middleware
│   └── monitor_service.py   # Background monitoring
├── api/
│   ├── sanitizers.py        # Input sanitization
│   └── secure_requests.py   # SSRF-safe HTTP
agent/
└── tools/
    └── llm_provider.py      # Multi-provider abstraction
scripts/
├── setup-alibaba-cloud-protection.sh  # Automated setup
├── dashboard.sh                       # Live monitoring
├── emergency-shutdown.sh              # Emergency stop
└── systemd/
    └── credit-protection.service      # System service
```

---

## 🔐 Security Features

### **1. Prompt Injection Prevention**
Detects and blocks dangerous patterns:
- `ignore previous instructions`
- `system: you are`
- `execute()` / `eval()`
- XSS attempts

### **2. SSRF Protection**
Blocks requests to:
- Private IP ranges (10.0.0.0/8, 192.168.0.0/16)
- Localhost (127.0.0.1)
- Link-local addresses
- Cloud metadata endpoints

### **3. Input Sanitization**
- Null byte removal
- Whitespace normalization
- Filename path traversal prevention
- Length limits (configurable)

---

## 📈 Tier Comparison

| Feature | FREE | ECONOMY | STANDARD | PREMIUM |
|---------|------|---------|----------|----------|
| **Daily Requests** | 50 | 100 | 300 | 500 |
| **Daily Tokens** | 25k | 50k | 150k | 300k |
| **Daily Cost Limit** | $0.25 | $0.50 | $2.00 | $5.00 |
| **Max Request Tokens** | 2k | 4k | 8k | 16k |
| **Hourly Burst** | 10 req | 20 req | 50 req | 100 req |
| **Circuit Breaker** | ✅ | ✅ | ✅ | ✅ |
| **Email Alerts** | ✅ | ✅ | ✅ | ✅ |
| **Webhook Alerts** | ✅ | ✅ | ✅ | ✅ |

---

## 🛠️ Troubleshooting

### **Service won't start**
```bash
# Check logs
sudo journalctl -u credit-protection -n 50

# Verify configuration
python3 -c "from vaal_ai_empire.credit_protection import get_manager; print(get_manager())"

# Check permissions
ls -la /var/lib/vaal/credit_protection
```

### **HuggingFace token errors**
```bash
# Verify token
huggingface-cli whoami

# Or test manually
python3 -c "from huggingface_hub import HfApi; HfApi().whoami()"
```

### **Circuit breaker stuck**
```bash
# Manually reset
python3 << 'PYTHON'
from vaal_ai_empire.credit_protection import get_manager
manager = get_manager()
manager.circuit_open = False
print("Circuit breaker reset")
PYTHON
```

### **Reset daily usage**
```bash
python3 << 'PYTHON'
from vaal_ai_empire.credit_protection import get_manager
manager = get_manager()
manager.reset_daily_usage()
print("Daily usage reset")
PYTHON
```

---

## 📝 License

MIT License - See LICENSE file for details

---

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Submit a pull request

---

## 🆘 Support

- **Issues**: https://github.com/deedk822-lang/The-lab-verse-monitoring-/issues
- **Discussions**: https://github.com/deedk822-lang/The-lab-verse-monitoring-/discussions
- **Email**: deedk822@gmail.com

---

## 🙏 Acknowledgments

- **HuggingFace**: For excellent transformer models
- **Alibaba Cloud**: Cloud infrastructure
- **FastAPI**: Modern Python web framework
- **Kimi AI**: Automated code enhancement

---

**Built with ❤️ for cost-conscious LLM deployments**

*Protect your credits. Scale with confidence.* 🛡️
