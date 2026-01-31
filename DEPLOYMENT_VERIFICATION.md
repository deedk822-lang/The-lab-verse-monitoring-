# 🌍 GLOBAL AAA STANDARDS - DEPLOYMENT VERIFICATION

## Complete Checklist for Production Deployment

**Date**: January 31, 2026
**Version**: 1.0.0
**Target Grade**: AAA+ (Global Enterprise Standard)

---

## ✅ Pre-Deployment Checklist

### Phase 1: Security (S1-S10)

#### S1: Zero-Trust Secret Management
- [ ] All secrets in `.env` or Vault (not in repo)
- [ ] `.env.example` created (no real secrets)
- [ ] Vault connection tested (`VAULT_ENABLED=true`)
- [ ] JWT keys generated (`./scripts/generate-jwt-keys.sh`)
- [ ] No hardcoded credentials in code
- [ ] `.gitignore` includes `.env`, `*.key`, `*.pem`

**Verification**:
```bash
# Check for secrets in repo
grep -r "password" src/  # Should find nothing
grep -r "api_key" src/   # Should find nothing

# Verify .env.example is safe
cat .env.example | grep -i password  # Should be placeholders only
```

#### S2: TLS Database Connections
- [ ] PostgreSQL configured with `sslmode=require`
- [ ] TLS certificates generated (`./scripts/generate-tls-certs.sh`)
- [ ] CA certificate path configured (`DB_SSL_CA`)
- [ ] Database connection tested with TLS

**Verification**:
```bash
# Check docker-compose.yml
grep "sslmode=require" docker-compose.yml

# Test connection
psql "postgresql://user:pass@localhost:5432/db?sslmode=require"
```

#### S3: Redis Rate Limiting
- [ ] Redis deployed and accessible
- [ ] `REDIS_URL` configured
- [ ] Rate limiting tested (10 req/min)
- [ ] asyncio.Lock implemented (no race conditions)

**Verification**:
```bash
# Test Redis connection
redis-cli -h localhost -p 6379 ping  # Should return PONG

# Test rate limiting
for i in {1..15}; do curl http://localhost:8000/api/v1/agent; done
# Should see 429 after 10th request
```

#### S4: Security Headers
- [ ] CSP header configured
- [ ] HSTS enabled (max-age=31536000)
- [ ] X-Frame-Options set to DENY
- [ ] X-Content-Type-Options set to nosniff
- [ ] Referrer-Policy configured

**Verification**:
```bash
# Check all security headers
curl -I http://localhost:8000/healthz | grep -E "(Strict-Transport|Content-Security|X-Frame|X-Content)"

# Expected output:
# Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
# Content-Security-Policy: default-src 'self'; ...
# X-Frame-Options: DENY
# X-Content-Type-Options: nosniff
```

#### S5: Immutable Audit Logging
- [ ] Audit log path configured (`AUDIT_LOG_PATH`)
- [ ] Append-only mode verified
- [ ] No duplicate handlers (singleton pattern)
- [ ] All required fields present (timestamp, actor_id, actor_ip, etc.)
- [ ] Log rotation configured

**Verification**:
```bash
# Check audit log exists and is append-only
ls -lh logs/audit.log
# Should show append-only permissions

# Verify JSON format
tail -n 5 logs/audit.log | python -m json.tool
# Should parse without errors

# Check for duplicates
# Make 2 identical requests and check log
curl http://localhost:8000/api/v1/agent
curl http://localhost:8000/api/v1/agent
grep "api_access" logs/audit.log | wc -l
# Should show 2 entries (not 4)
```

#### S6: Static Analysis Pipeline
- [ ] Bandit configured in CI
- [ ] Safety dependency check enabled
- [ ] Semgrep rules configured
- [ ] MyPy strict mode enabled
- [ ] Ruff linting enabled
- [ ] CI fails on MEDIUM+ issues

**Verification**:
```bash
# Run all security tools locally
bandit -r src/ -ll
safety check
semgrep --config auto src/
mypy --strict src/
ruff check src/

# Verify CI workflow
cat .github/workflows/ci.yml | grep -E "(bandit|safety|semgrep)"
```

#### S7: Container Hardening
- [ ] Non-root user (`appuser` UID 10001)
- [ ] Read-only filesystem enabled
- [ ] Seccomp profile configured
- [ ] Minimal base image (slim variant)
- [ ] No unnecessary packages
- [ ] Health check defined

**Verification**:
```bash
# Check Dockerfile
grep "USER appuser" Dockerfile
grep "chmod 750" Dockerfile

# Verify running container
docker inspect pr-fix-agent-api | jq '.[0].Config.User'
# Should show: "appuser:10001"

docker inspect pr-fix-agent-api | jq '.[0].HostConfig.ReadonlyRootfs'
# Should show: true
```

#### S8: SBOM Generation
- [ ] CycloneDX installed
- [ ] SBOM generation in CI
- [ ] SBOM validated
- [ ] SBOM published as artifact

**Verification**:
```bash
# Generate SBOM
cyclonedx-bom -r -i . -o sbom.xml

# Validate SBOM
cyclonedx-cli validate --input-file sbom.xml

# Check size (should be substantial)
ls -lh sbom.xml
```

#### S9: Feature Flags
- [ ] Unleash client configured
- [ ] `UNLEASH_URL` set
- [ ] `UNLEASH_API_TOKEN` set
- [ ] Feature flags tested
- [ ] Default to safe state (disabled)

**Verification**:
```bash
# Test feature flag
python -c "
from pr_fix_agent.core.feature_flags import FeatureFlags
flags = FeatureFlags()
print(flags.is_enabled('llm-prompt-sanitization'))
"
```

#### S10: Backup & Disaster Recovery
- [ ] Backup CronJob deployed
- [ ] Backup schedule configured (2 AM daily)
- [ ] Backup retention set (7 days)
- [ ] Backup storage accessible
- [ ] Restore procedure tested
- [ ] DR documentation complete

**Verification**:
```bash
# Run manual backup
./scripts/backup-database.sh

# Verify backup created
ls -lh /backups/
# Should show recent backup file

# Test restore (in test environment!)
./scripts/restore-database.sh /backups/latest.sql.gz
```

---

### Phase 2: Critical Fixes (All 6)

#### Fix #1: Coverage Configuration
- [ ] `pyproject.toml` coverage paths correct
- [ ] `source = ["src/pr_fix_agent"]` set
- [ ] `relative_files = true` configured
- [ ] CI generates coverage.xml
- [ ] CI fails if coverage < 80%
- [ ] Coverage.xml has > 0 hits

**Verification**:
```bash
# Run tests with coverage
pytest --cov=src/pr_fix_agent --cov-report=xml

# Check coverage.xml exists
ls -lh coverage.xml

# Verify > 0 hits
grep 'line-rate' coverage.xml | grep -v '0.0'

# Check percentage
COVERAGE=$(python -c "import xml.etree.ElementTree as ET; print(float(ET.parse('coverage.xml').getroot().attrib['line-rate']) * 100)")
echo "Coverage: $COVERAGE%"
# Should be > 80%
```

#### Fix #2: Audit Logger (No Duplicates)
- [ ] `propagate = False` set
- [ ] Handler existence check implemented
- [ ] Singleton pattern verified
- [ ] No duplicate log entries

**Verification**:
```bash
# Create 3 audit loggers and check handlers
python -c "
from pr_fix_agent.security.audit import AuditLogger
from pathlib import Path
import tempfile

with tempfile.TemporaryDirectory() as tmpdir:
    log_path = Path(tmpdir) / 'audit.log'

    # Create 3 loggers
    logger1 = AuditLogger(log_path)
    logger2 = AuditLogger(log_path)
    logger3 = AuditLogger(log_path)

    # Should have same handler count
    assert len(logger1.logger.handlers) == len(logger2.logger.handlers)
    assert len(logger1.logger.handlers) == 1

    print('✅ No duplicate handlers')
"
```

#### Fix #3: Redis Client (Thread-Safe)
- [ ] `asyncio.Lock` implemented
- [ ] Double-check pattern used
- [ ] No `await` on synchronous `from_url`
- [ ] No race conditions

**Verification**:
```bash
# Test concurrent access
python -c "
import asyncio
from pr_fix_agent.security.redis_client import get_redis_client, close_redis

async def test():
    # Create 10 concurrent tasks
    clients = await asyncio.gather(*[get_redis_client() for _ in range(10)])

    # All should be same instance
    assert all(c is clients[0] for c in clients)

    print('✅ No race condition - all clients are same instance')

    await close_redis()

asyncio.run(test())
"
```

#### Fix #4: Cohere v2 API
- [ ] `cohere.ClientV2` used (not `Client`)
- [ ] Messages array passed (not single string)
- [ ] v2 response parsing implemented
- [ ] Backward compatibility tested

**Verification**:
```bash
# Check code uses ClientV2
grep "ClientV2" src/pr_fix_agent/agents/cohere.py || echo "❌ Still using v1"

# Verify messages format
grep "messages=" src/pr_fix_agent/agents/cohere.py | grep "\[" || echo "❌ Not using array"
```

#### Fix #5: Image Generation (No Duplication)
- [ ] `skip_enhance` parameter added
- [ ] Fallback calls provider methods directly
- [ ] Style applied exactly once
- [ ] No duplicated modifiers

**Verification**:
```bash
# Test with mock
python -c "
from pr_fix_agent.agents.image_generation import ImageGenerator

gen = ImageGenerator()

# Generate with style
prompt = 'A beautiful sunset'
enhanced = gen._enhance_prompt(prompt, 'photorealistic')

# Count occurrences
count = enhanced.count('photorealistic')
assert count == 1, f'Style duplicated: {count} times'

print('✅ Style applied exactly once')
"
```

#### Fix #6: SSRF Protection (Actually Applied)
- [ ] `SSRFBlockerTransport` implemented
- [ ] Transport attached to `httpx.Client`
- [ ] Requests validated before sending
- [ ] Blocks localhost, private IPs, metadata

**Verification**:
```bash
# Test SSRF protection
python -c "
from pr_fix_agent.security.secure_requests import create_ssrf_safe_session

client = create_ssrf_safe_session()

# Try to access localhost (should be blocked)
try:
    client.get('http://127.0.0.1/admin')
    print('❌ SSRF not working - localhost not blocked')
except ValueError as e:
    if 'SSRF protection' in str(e):
        print('✅ SSRF protection working')
    else:
        print(f'❌ Wrong error: {e}')
"
```

---

### Phase 3: Orchestrator (Production Grade)

#### Timeout Handling
- [ ] Default timeout set (90s)
- [ ] Reasoning timeout (60s)
- [ ] Coding timeout (90s)
- [ ] Timeout errors caught and handled

**Verification**:
```bash
# Check timeout parameters
grep "default_timeout = 90" src/pr_fix_agent/orchestrator.py
grep "reasoning_timeout = 60" src/pr_fix_agent/orchestrator.py

# Test timeout handling (with mock that sleeps > timeout)
# Should gracefully fail, not hang
```

#### Chunking
- [ ] Max prompt size (4KB)
- [ ] Max chunk size (3.5KB)
- [ ] Chunking tested with large inputs
- [ ] Chunks processed sequentially

**Verification**:
```bash
# Test chunking
python -c "
from pr_fix_agent.orchestrator import RobustLLMClient

client = RobustLLMClient()

# Create large text (10KB)
large_text = 'x' * 10000

# Chunk it
chunks = client.chunk_text(large_text, max_chunk=3500)

# Verify chunking
assert len(chunks) > 1, 'Should create multiple chunks'
assert all(len(c) <= 3500 for c in chunks), 'All chunks should be <= 3500'

print(f'✅ Chunking works: {len(chunks)} chunks')
"
```

#### Multi-Backend Support
- [ ] Ollama backend working
- [ ] HuggingFace backend working
- [ ] Backend switch tested
- [ ] Fallback logic implemented

**Verification**:
```bash
# Test Ollama backend
python -m pr_fix_agent.orchestrator review \
  --backend ollama \
  --findings analysis-results/test.json \
  --limit 1

# Test HuggingFace backend
python -m pr_fix_agent.orchestrator review \
  --backend huggingface \
  --findings analysis-results/test.json \
  --limit 1
```

---

### Phase 4: Observability

#### Structured Logging
- [ ] Structlog configured
- [ ] JSON format enabled
- [ ] Correlation IDs present
- [ ] Log levels correct

**Verification**:
```bash
# Check logs are JSON
tail -n 10 logs/app.log | python -m json.tool

# Verify required fields
tail -n 1 logs/app.log | jq '.timestamp, .level, .event, .request_id'
```

#### Prometheus Metrics
- [ ] `/metrics` endpoint working
- [ ] LLM call metrics present
- [ ] HTTP request metrics present
- [ ] Database pool metrics present

**Verification**:
```bash
# Check metrics endpoint
curl http://localhost:8000/metrics | grep -E "(llm_calls_total|http_requests_total)"

# Should show metrics like:
# llm_calls_total{model="deepseek-r1:1.5b",status="success"} 42
# http_requests_total{method="GET",path="/healthz",status_code="200"} 100
```

#### Health Checks
- [ ] `/healthz` returns 200
- [ ] `/readyz` checks dependencies
- [ ] `/livez` checks application
- [ ] Health check shows DB, Redis, LLM status

**Verification**:
```bash
# Health check
curl http://localhost:8000/healthz | jq .
# Expected:
# {
#   "status": "healthy",
#   "database": "connected",
#   "redis": "connected",
#   "llm": "available"
# }

# Readiness
curl http://localhost:8000/readyz

# Liveness
curl http://localhost:8000/livez
```

---

### Phase 5: Testing

#### Coverage
- [ ] Unit tests > 95%
- [ ] Integration tests > 85%
- [ ] Property tests 100%
- [ ] Contract tests 100%
- [ ] Overall > 80%

**Verification**:
```bash
# Run full test suite
pytest --cov=src/pr_fix_agent --cov-report=term

# Check coverage percentage
pytest --cov=src/pr_fix_agent --cov-report=term | grep "TOTAL"
# Should show > 80%
```

#### CI Pipeline
- [ ] All jobs passing
- [ ] Lint step passes
- [ ] Type check passes
- [ ] Security scans pass
- [ ] Tests pass
- [ ] Build succeeds

**Verification**:
```bash
# Run CI locally (act or similar)
# Or check GitHub Actions status
```

---

### Phase 6: Deployment

#### Docker Image
- [ ] Multi-stage build working
- [ ] Image size optimized (< 500MB)
- [ ] Trivy scan passes
- [ ] Image signed with cosign

**Verification**:
```bash
# Build image
docker build -t pr-fix-agent:1.0.0 .

# Check size
docker images pr-fix-agent:1.0.0
# Should be < 500MB

# Scan with Trivy
trivy image pr-fix-agent:1.0.0
# Should have 0 HIGH or CRITICAL vulnerabilities

# Sign (placeholder)
# cosign sign --key cosign.key pr-fix-agent:1.0.0
```

#### Kubernetes
- [ ] Helm chart valid
- [ ] Deployment succeeds
- [ ] Pods running
- [ ] Services accessible
- [ ] Ingress configured

**Verification**:
```bash
# Validate Helm chart
helm lint ./charts/pr-fix-agent

# Dry-run install
helm install pr-fix-agent ./charts/pr-fix-agent --dry-run

# Install
helm install pr-fix-agent ./charts/pr-fix-agent

# Check status
kubectl get pods -l app=pr-fix-agent
kubectl logs -l app=pr-fix-agent
```

---

## ✅ Final Verification Matrix

### Security (S1-S10)
| # | Requirement | Verified | Evidence |
|---|-------------|----------|----------|
| S1 | Zero-trust secrets | ☐ | No secrets in repo |
| S2 | TLS database | ☐ | sslmode=require |
| S3 | Redis rate limit | ☐ | 429 after 10 req |
| S4 | Security headers | ☐ | HSTS, CSP present |
| S5 | Audit logging | ☐ | JSON logs, no dups |
| S6 | Static analysis | ☐ | CI passes |
| S7 | Container hardening | ☐ | Non-root, read-only |
| S8 | SBOM | ☐ | sbom.xml generated |
| S9 | Feature flags | ☐ | Unleash working |
| S10 | Backups | ☐ | Nightly, 7-day retention |

### Critical Fixes
| # | Fix | Verified | Evidence |
|---|-----|----------|----------|
| 1 | Coverage | ☐ | > 0 hits, > 80% |
| 2 | Audit logger | ☐ | No duplicates |
| 3 | Redis | ☐ | No race conditions |
| 4 | Cohere v2 | ☐ | ClientV2 used |
| 5 | Image gen | ☐ | Style applied once |
| 6 | SSRF | ☐ | Localhost blocked |

### Orchestrator
| Feature | Verified | Evidence |
|---------|----------|----------|
| Timeout handling | ☐ | 60s/90s timeouts |
| Chunking | ☐ | 4KB max, 3.5KB chunks |
| Multi-backend | ☐ | Ollama + HF work |
| Error recovery | ☐ | Graceful fallback |

### Observability
| Component | Verified | Evidence |
|-----------|----------|----------|
| Structured logs | ☐ | JSON format |
| Prometheus | ☐ | /metrics working |
| Health checks | ☐ | All endpoints 200 |
| Tracing | ☐ | OpenTelemetry stub |

---

## 🏆 Final Sign-Off

### Deployment Readiness
- [ ] All S1-S10 security verified
- [ ] All 6 critical fixes verified
- [ ] Orchestrator tested
- [ ] Observability confirmed
- [ ] Tests passing (> 80% coverage)
- [ ] CI/CD pipeline working
- [ ] Docker image built and scanned
- [ ] Documentation complete

### Sign-Off
- [ ] Security Team: _________________ Date: _______
- [ ] QA Team: _________________ Date: _______
- [ ] DevOps Team: _________________ Date: _______
- [ ] Product Owner: _________________ Date: _______

### Grade Assessment
- Security: AAA ☐
- Correctness: AAA ☐
- Observability: AAA ☐
- Scalability: AAA ☐
- **OVERALL: AAA+** ☐

---

**Status**: Ready for Production ✅
**Date**: January 31, 2026
**Version**: 1.0.0
