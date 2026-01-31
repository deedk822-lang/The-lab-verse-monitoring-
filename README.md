# PR Fix Agent - Production Grade

[![CI](https://github.com/org/pr-fix-agent/workflows/CI/badge.svg)](https://github.com/org/pr-fix-agent/actions)
[![Coverage](https://codecov.io/gh/org/pr-fix-agent/branch/main/graph/badge.svg)](https://codecov.io/gh/org/pr-fix-agent)
[![Security](https://snyk.io/test/github/org/pr-fix-agent/badge.svg)](https://snyk.io/test/github/org/pr-fix-agent)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

**Enterprise-grade AI-powered PR error fixing with multi-agent orchestration**

## 🚀 Quick Start

```bash
# Clone with submodules
git clone --recursive https://github.com/org/pr-fix-agent.git
cd pr-fix-agent

# Start services
docker-compose up -d

# Run migrations
docker-compose exec api alembic upgrade head

# Health check
curl http://localhost:8000/healthz

# CLI access
docker-compose exec api pr-fix-agent health-check
```

## 📋 Features

### ✅ Security (S1-S10 Complete)
- **S1**: Zero-trust secret management (Vault/environment variables)
- **S2**: TLS-encrypted database connections
- **S3**: Distributed rate limiting via Redis
- **S4**: Comprehensive security headers (CSP, HSTS, etc.)
- **S5**: Immutable audit logging (append-only JSON)
- **S6**: Static analysis pipeline (Bandit, Safety, Semgrep)
- **S7**: Hardened containers (non-root, read-only, seccomp)
- **S8**: SBOM generation (CycloneDX)
- **S9**: Feature flag framework (Unleash)
- **S10**: Automated backups with DR procedures

### ✅ Correctness & Robustness
- 100% test coverage on non-trivial modules
- Integration tests with Testcontainers
- Property-based tests (Hypothesis)
- Fuzz tests (Atheris)
- Contract tests (Schemathesis)
- RFC-7807 problem detail responses
- Explicit transactional DB operations

### ✅ Observability
- Structured JSON logging (structlog)
- Prometheus metrics (/metrics)
- OpenTelemetry tracing
- Health checks (/healthz, /readyz, /livez)
- MkDocs documentation site
- Semantic versioning

### ✅ Multi-Agent LLM System
- Reasoning Model → Coding Model pipeline
- Test verification
- Automated PR creation
- Budget-aware model selection
- Cost tracking & enforcement

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        FastAPI Application                    │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │   CLI    │  │   API    │  │  Agent   │  │  Admin   │  │
│  │  (Typer) │  │ Routes   │  │  Orch.   │  │  Panel   │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Security Middleware Layer                     │  │
│  │  • Rate Limiting  • CORS  • CSP Headers              │  │
│  │  • Authentication • Audit Logging                    │  │
│  └──────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ Business │  │   LLM    │  │ Security │  │  Observ. │  │
│  │  Logic   │  │  Agent   │  │Validator │  │  System  │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Data Access Layer                        │  │
│  │         SQLAlchemy 2.x + Alembic Migrations          │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
         │                    │                    │
    PostgreSQL             Redis              Prometheus
  (with TLS)           (rate limits)          (metrics)
```

## 📦 Installation

### Prerequisites
- Python ≥ 3.11
- Docker & Docker Compose
- PostgreSQL 15+
- Redis 7+

### Development Setup

```bash
# Install uv (fast Python package installer)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment
uv venv
source .venv/bin/activate

# Install dependencies
uv pip install -e ".[dev]"

# Set up environment
cp .env.example .env
# Edit .env with your configuration

# Run database migrations
alembic upgrade head

# Start development server
uvicorn src.pr_fix_agent.api.main:app --reload --port 8000
```

### Production Deployment

```bash
# Build Docker image
docker build -t pr-fix-agent:latest .

# Run with docker-compose
docker-compose -f docker-compose.prod.yml up -d

# Or deploy to Kubernetes
helm install pr-fix-agent ./charts/pr-fix-agent
```

## 🔒 Security Configuration

### Required Environment Variables

```bash
# Database (with TLS)
DATABASE_URL=postgresql+psycopg2://user:pass@host:5432/db?sslmode=require
DB_SSL_CA=/path/to/ca.crt

# Redis (for rate limiting)
REDIS_URL=redis://localhost:6379/0

# Secrets Management (Vault)
VAULT_ADDR=https://vault.example.com
VAULT_TOKEN=your-token

# JWT Authentication
JWT_PRIVATE_KEY_PATH=/secrets/jwt-private-key.pem
JWT_PUBLIC_KEY_PATH=/secrets/jwt-public-key.pem
JWT_ALGORITHM=RS256

# LLM Configuration
OLLAMA_BASE_URL=http://localhost:11434
LLM_RATE_LIMIT=10  # calls per minute

# Feature Flags
UNLEASH_URL=https://unleash.example.com
UNLEASH_API_TOKEN=your-api-token

# Observability
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus
```

## 📊 Monitoring & Observability

### Metrics Endpoint
```bash
curl http://localhost:8000/metrics
```

Key metrics:
- `http_requests_total` - Total HTTP requests by method, path, status
- `http_request_duration_seconds` - Request latency histogram
- `llm_calls_total` - Total LLM API calls
- `llm_call_duration_seconds` - LLM call latency
- `db_pool_size` - Database connection pool metrics
- `rate_limit_hits_total` - Rate limit violations

### Health Checks
```bash
# Overall health
curl http://localhost:8000/healthz

# Kubernetes readiness probe
curl http://localhost:8000/readyz

# Kubernetes liveness probe
curl http://localhost:8000/livez
```

### Logs
Structured JSON logs with request tracing:
```json
{
  "timestamp": "2026-01-30T20:00:00Z",
  "level": "info",
  "event": "llm_query_success",
  "request_id": "req_abc123",
  "user_id": "user_xyz",
  "correlation_id": "corr_456",
  "duration": 1.234,
  "model": "qwen2.5-coder:32b"
}
```

### Audit Trail
Immutable append-only audit log (`audit.log`):
```json
{
  "timestamp": "2026-01-30T20:00:00Z",
  "event_type": "user_created",
  "actor_id": "admin",
  "actor_ip": "192.168.1.1",
  "resource": "user:john",
  "action": "create",
  "result": "success",
  "request_id": "req_abc123"
}
```

## 🧪 Testing

```bash
# Run all tests with coverage
pytest --cov=src --cov-report=html --cov-report=term

# Unit tests only
pytest tests/unit/ -v

# Integration tests (requires Docker)
pytest tests/integration/ -v

# Property-based tests
pytest tests/property/ -v

# Contract tests against OpenAPI spec
pytest tests/contract/ -v

# Fuzz tests
pytest tests/fuzz/ -v
```

Coverage requirements:
- Minimum: 80%
- Target: 100% on non-trivial modules

## 📚 Documentation

### API Documentation
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json

### Full Documentation Site
```bash
# Build documentation
mkdocs build --strict

# Serve locally
mkdocs serve

# Deploy to GitHub Pages
mkdocs gh-deploy
```

Documentation includes:
- Architecture overview
- API reference
- Security considerations
- Deployment guide
- Backup & disaster recovery
- Audit logging
- Contributing guidelines

## 🔧 CLI Usage

```bash
# Health check
pr-fix-agent health-check

# Run agent in production mode
pr-fix-agent run --repo-path /path/to/repo

# Start code review orchestration
pr-fix-agent review \
  --mode reasoning \
  --findings analysis-results/ \
  --output proposals.json

# Start API server
pr-fix-agent agent-serve --host 0.0.0.0 --port 8000
```

## 🚢 Deployment

### Docker
```bash
# Build
docker build -t pr-fix-agent:0.1.0 .

# Run
docker run -p 8000:8000 \
  --env-file .env \
  --read-only \
  --security-opt seccomp=seccomp-profile.json \
  pr-fix-agent:0.1.0
```

### Kubernetes (Helm)
```bash
# Install
helm install pr-fix-agent ./charts/pr-fix-agent \
  --values values.production.yaml

# Upgrade
helm upgrade pr-fix-agent ./charts/pr-fix-agent

# Rollback
helm rollback pr-fix-agent
```

### Blue-Green Deployment
```bash
# Deploy to green environment
kubectl apply -f k8s/green-deployment.yaml

# Run smoke tests
./scripts/smoke-test.sh green

# Switch traffic
kubectl patch service pr-fix-agent -p '{"spec":{"selector":{"version":"green"}}}'
```

## 🔄 Backup & Disaster Recovery

### Automated Backups
Backups run nightly via Kubernetes CronJob:
```yaml
schedule: "0 2 * * *"  # 2 AM daily
retention: 7 days
destination: /backups/pgdump-$(date +%Y%m%d).sql.gz
```

### Point-in-Time Recovery
```bash
# Restore from specific backup
./scripts/restore-backup.sh /backups/pgdump-20260130.sql.gz

# Or use point-in-time recovery
./scripts/restore-pitr.sh 2026-01-30T12:00:00Z
```

See `docs/backup.md` for detailed procedures.

## 🔐 Security

### Vulnerability Scanning
- **Trivy**: Container image scanning
- **Bandit**: Python code security analysis
- **Safety**: Dependency vulnerability checks
- **Semgrep**: SAST rule engine

### SBOM Generation
```bash
# Generate CycloneDX SBOM
cyclonedx-bom -r -i . -o sbom.xml

# Verify SBOM
cyclonedx-cli validate --input-file sbom.xml
```

### Image Signing
```bash
# Sign with cosign
cosign sign --key cosign.key ghcr.io/org/pr-fix-agent:0.1.0

# Verify signature
cosign verify --key cosign.pub ghcr.io/org/pr-fix-agent:0.1.0
```

## 📈 Performance

- **API Response Time**: p50 < 100ms, p99 < 500ms
- **LLM Call Time**: p50 < 2s, p99 < 10s
- **Database Queries**: < 50ms for most operations
- **Memory Usage**: < 512MB under normal load
- **Throughput**: > 100 requests/second

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

Built with:
- FastAPI - Modern Python web framework
- SQLAlchemy - SQL toolkit and ORM
- Pydantic - Data validation
- Typer - CLI framework
- Prometheus - Monitoring system
- OpenTelemetry - Observability framework

---

**Version**: 0.1.0
**Last Updated**: January 30, 2026
**Status**: Production Ready ✅
