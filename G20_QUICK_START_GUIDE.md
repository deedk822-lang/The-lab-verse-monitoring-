# VAAL AI Empire - Quick Start Guide

## 🚀 Overview

This enhanced version includes:

### Security Enhancements
- ✅ **Prompt Injection Mitigation**: Multi-layered sanitization with pattern detection
- ✅ **SSRF Protection**: URL validation, private IP blocking, metadata endpoint protection
- ✅ **Command Injection Prevention**: Removed `shell=True`, tokenized commands
- ✅ **Secret Management**: Environment-based configuration, no hardcoded keys
- ✅ **Authentication Hardening**: JWT tokens, API key validation, webhook signatures
- ✅ **Rate Limiting**: Per-client request throttling
- ✅ **Webhook Deduplication**: TTL-based event deduplication

### Multi-Provider LLM Support
- 🤖 **HuggingFace**: Local model inference
- 🌐 **Z.AI**: Cloud-based inference
- 🎯 **Qwen/Dashscope**: Alibaba Cloud models
- 🔵 **OpenAI**: GPT-4, GPT-4o, GPT-4o-mini
- 🟣 **Anthropic**: Claude models (extendable)

### Operational Improvements
- 📊 **Monitoring**: Prometheus metrics, Grafana dashboards
- 🐳 **Docker**: Multi-stage builds, GPU support, health checks
- ☸️ **Kubernetes**: Production-ready manifests with HPA, NetworkPolicy, PDB
- 🔄 **CI/CD**: GitHub Actions pipeline with testing, security scanning
- 💾 **Database**: Schema migrations, usage tracking, cost attribution
- 📝 **Logging**: Structured logging with security audit trail

## 📋 Prerequisites

- Python 3.10+
- Docker & Docker Compose
- PostgreSQL 15+
- Redis 7+
- (Optional) NVIDIA GPU with CUDA 12.1+
- (Optional) Kubernetes cluster for production

## 🛠️ Installation

### Option 1: Quick Setup with Script

```bash
# Clone repository
git clone https://github.com/yourusername/vaal-ai-empire.git
cd vaal-ai-empire

# Run setup script
chmod +x scripts/setup-agent.sh
./scripts/setup-agent.sh

# Optional: Download models
DOWNLOAD_MODELS=true ./scripts/setup-agent.sh

# Optional: Setup monitoring
SETUP_MONITORING=true ./scripts/setup-agent.sh
```

### Option 2: Manual Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment configuration
cp .env.example .env

# Edit .env with your configuration
nano .env

# Initialize database
docker-compose up -d postgres
psql -h localhost -U vaaluser -d vaal_ai_empire -f vaal_ai_empire/update_schema.sql
```

### Option 3: Docker Compose (Recommended for Development)

```bash
# Copy environment file
cp .env.example .env

# Edit configuration
nano .env

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f app

# Check health
curl http://localhost:8000/health
```

## 🔧 Configuration

### Essential Environment Variables

```bash
# Core
SECRET_KEY=your-secret-key-change-this
LLM_PROVIDER=openai  # or huggingface, zai, qwen

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/vaal_ai_empire

# Redis
REDIS_URL=redis://:pass@localhost:6379/0

# Security
SELF_HEALING_KEY=your-webhook-secret
JWT_SECRET_KEY=your-jwt-secret

# LLM Providers (configure as needed)
OPENAI_API_KEY=sk-...
HF_TOKEN=hf_...
ZAI_API_KEY=zai_...
QWEN_API_KEY=qwen_...
```

### Provider Selection

Edit `.env` to choose your LLM provider:

```bash
# For OpenAI
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-key

# For HuggingFace (local)
LLM_PROVIDER=huggingface
HF_TOKEN=hf_your_token
HF_DEVICE=cuda  # or cpu

# For Z.AI
LLM_PROVIDER=zai
ZAI_API_KEY=your-zai-key

# For Qwen
LLM_PROVIDER=qwen
QWEN_API_KEY=your-qwen-key
```

## 🚀 Running the Application

### Development Mode

```bash
# Activate virtual environment
source venv/bin/activate

# Run with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode (Docker)

```bash
# Start services
docker-compose up -d

# Scale application
docker-compose up -d --scale app=3

# View logs
docker-compose logs -f app
```

### Production Mode (Kubernetes)

```bash
# Apply configurations
kubectl apply -f k8s/

# Check deployment status
kubectl get pods -n vaal-ai-empire

# View logs
kubectl logs -f deployment/vaal-app -n vaal-ai-empire

# Scale replicas
kubectl scale deployment vaal-app --replicas=5 -n vaal-ai-empire
```

## 🧪 Testing

### Run All Tests

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests with coverage
pytest tests/ -v --cov=vaal_ai_empire --cov=agent --cov=app

# Run specific test suite
pytest tests/test_security.py -v

# Run integration tests
pytest tests/integration/ -v
```

### Security Testing

```bash
# Check for vulnerabilities
safety check

# Run security scanner
bandit -r vaal_ai_empire agent app

# Test SSRF protection
pytest tests/test_security.py::TestSSRFProtection -v
```

## 📊 Monitoring

### Access Dashboards

- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9091
- **pgAdmin**: http://localhost:5050 (admin@vaal.ai/changeme)
- **Redis Commander**: http://localhost:8081

### Metrics Endpoint

```bash
curl http://localhost:8000/metrics
```

### Health Checks

```bash
# Liveness
curl http://localhost:8000/health

# Readiness
curl http://localhost:8000/ready
```

## 🔐 Security Best Practices

### Before Production

1. **Generate Strong Secrets**:
   ```bash
   openssl rand -hex 32  # For SECRET_KEY
   openssl rand -hex 32  # For JWT_SECRET_KEY
   openssl rand -hex 32  # For SELF_HEALING_KEY
   ```

2. **Enable HTTPS**: Configure SSL certificates in nginx
3. **Review Firewall Rules**: Ensure only necessary ports are exposed
4. **Enable Rate Limiting**: Set appropriate limits in `.env`
5. **Configure Backups**: Set up automated database backups
6. **Audit Logs**: Review security audit logs regularly

### Security Checklist

- [ ] Changed all default passwords
- [ ] Generated strong random secrets
- [ ] Configured HTTPS/TLS
- [ ] Enabled rate limiting
- [ ] Set up database backups
- [ ] Configured monitoring alerts
- [ ] Reviewed NetworkPolicy rules
- [ ] Enabled security audit logging
- [ ] Tested SSRF protection
- [ ] Tested prompt injection prevention

## 📝 API Usage

### Generate Text

```bash
curl -X POST http://localhost:8000/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Write a Python function to sort a list",
    "task": "CODE_GENERATION",
    "max_tokens": 500,
    "temperature": 0.7
  }'
```

### Webhook Endpoint

```bash
curl -X POST http://localhost:8000/webhooks/atlassian \
  -H "Content-Type: application/json" \
  -H "X-Self-Healing-Key: your-webhook-secret" \
  -d '{
    "webhookEvent": "issue:updated",
    "issue": {
      "key": "PROJ-123",
      "fields": {
        "summary": "Bug in production"
      }
    }
  }'
```

## 🔄 Database Operations

### Run Migrations

```bash
# Using Docker
docker-compose exec app python -m alembic upgrade head

# Using Kubernetes
kubectl exec -n vaal-ai-empire deployment/vaal-app -- \
  python -m alembic upgrade head
```

### Backup Database

```bash
# Manual backup
docker-compose exec postgres pg_dump -U vaaluser vaal_ai_empire > backup.sql

# Using backup service
docker-compose --profile backup up backup
```

### Restore Database

```bash
docker-compose exec -T postgres psql -U vaaluser vaal_ai_empire < backup.sql
```

## 🐛 Troubleshooting

### Common Issues

**1. Database Connection Failed**
```bash
# Check if postgres is running
docker-compose ps postgres

# View logs
docker-compose logs postgres

# Test connection
psql -h localhost -U vaaluser -d vaal_ai_empire
```

**2. GPU Not Detected**
```bash
# Check NVIDIA driver
nvidia-smi

# Verify Docker GPU support
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi
```

**3. LLM Provider Errors**
```bash
# Check API key configuration
grep -i "api_key" .env

# Test provider connection
python -c "from agent.tools.llm_provider import get_global_provider; print(get_global_provider())"
```

**4. Rate Limit Issues**
```bash
# Increase rate limit in .env
RATE_LIMIT_REQUESTS_PER_MINUTE=120

# Restart services
docker-compose restart app
```

## 📚 Additional Resources

- **Architecture Documentation**: `docs/architecture.md`
- **API Documentation**: http://localhost:8000/docs
- **Security Guidelines**: `docs/security.md`
- **Deployment Guide**: `docs/deployment.md`
- **Contributing**: `CONTRIBUTING.md`

## 🤝 Support

- **Issues**: https://github.com/yourusername/vaal-ai-empire/issues
- **Discussions**: https://github.com/yourusername/vaal-ai-empire/discussions
- **Security**: security@yourdomain.com

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**Made with ❤️ by the VAAL AI Empire Team**
