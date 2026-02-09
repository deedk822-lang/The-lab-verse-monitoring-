# The-Lap-Verse-Monitoring: Quickstart Guide

## One-Line Summary
**Production-grade self-compete monitoring system with idempotency, SLO enforcement, FinOps tracking, and automatic champion evolution.**

## 60-Second Setup

### 1. Start Redis
```bash
docker run -d -p 6379:6379 redis:7-alpine
```

### 2. Install & Run
```bash
cd lapverse-core
npm install
npm run dev
```

You should see:
```
♛ TheLapVerseCore live
```

## Test It (3 Commands)

### Submit a Task
```bash
curl -X POST http://localhost:3000/api/v2/tasks \
  -H "Idempotency-Key: $(uuidgen)" \
  -H "X-Tenant-ID: acme" \
  -H "Content-Type: application/json" \
  -d '{"type":"ANALYSIS","priority":"high","description":"Test task","tenant":"acme","platforms":["twitter"]}'
```

### Launch Competition
```bash
curl -X POST http://localhost:3000/api/v2/self-compete \
  -H "Idempotency-Key: $(uuidgen)" \
  -H "X-Tenant-ID: acme" \
  -H "Content-Type: application/json" \
  -d '{"content":"Test compete","platforms":["twitter"],"priority":"high"}'
```

### Check Metrics
```bash
curl http://localhost:3000/metrics | grep lapverse
```

## What You Get

### Idempotency
- Duplicate requests return cached responses
- No accidental double-processing

### Cost Control
- Every request gets cost estimate
- Requests blocked if exceeding 70% margin

### SLO Protection
- System tracks burn-rate
- Sheds load when budget exhausted

### Circuit Breakers
- News AI fails gracefully (3s timeout)
- Share API fails gracefully (2s timeout)

### Self-Compete
- 4 variants battle automatically
- Champion auto-promoted
- Triggers Kaggle pipeline

### Observability
- OpenTelemetry traces
- Prometheus metrics
- Secure PII-redacted logs

## Project Structure

```
lapverse-core/
├── src/
│   ├── TheLapVerseCore.ts       # Main orchestrator
│   ├── index.ts                  # Entry point
│   ├── resilience/
│   │   └── CircuitBreaker.ts     # Fault tolerance
│   ├── middleware/
│   │   └── IdempotencyManager.ts # Duplicate prevention
│   ├── cost/
│   │   └── FinOpsTagger.ts       # Cost tracking
│   ├── reliability/
│   │   └── SloErrorBudget.ts     # SLO enforcement
│   ├── contracts/
│   │   └── OpenApiValidator.ts   # API validation
│   ├── delivery/
│   │   └── OpenFeatureFlags.ts   # Feature rollout
│   ├── security/
│   │   └── SecureLogger.ts       # PII redaction
│   └── kaggle/
│       └── TheLapVerseKagglePipe.ts # Model evolution
├── openapi/
│   └── lapverse.yaml             # OpenAPI 3.1 spec
├── package.json
├── tsconfig.json
├── IMPLEMENTATION.md             # Full documentation
└── QUICKSTART.md                 # This file
```

## Key Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| POST | /api/v2/tasks | Submit task with FinOps tracking |
| POST | /api/v2/self-compete | Launch competition |
| GET | /api/v2/self-compete/:id | Get competition status |
| GET | /api/status | System health |
| GET | /metrics | Prometheus metrics |

## Next Steps

1. **Read** `IMPLEMENTATION.md` for full details
2. **Review** `openapi/lapverse.yaml` for API spec
3. **Connect** real News AI and Share API clients
4. **Configure** Prometheus scraping
5. **Deploy** to production

## Troubleshooting

### Port already in use
```bash
export PORT=3001
npm run dev
```

### Redis connection refused
```bash
docker ps | grep redis
# If not running:
docker run -d -p 6379:6379 redis:7-alpine
```

### Build errors
```bash
rm -rf node_modules dist
npm install
npm run build
```

## Production Deployment

```bash
# Build
npm run build

# Run
export NODE_ENV=production
export PORT=3000
export REDIS_URL=redis://prod-redis:6379
npm start
```

## Key Metrics to Monitor

- `lapverse_win_rate` - Champion performance delta
- `lapverse_budget_burn_rate` - SLO health
- `lapverse_cost_per_competition` - Unit economics
- `lapverse_tasks_total` - Throughput
- `lapverse_task_duration_ms` - Latency

## Architecture Highlights

### The Self-Compete Loop
```
Request → Cost Check → SLO Check → Feature Gate → Queue
                ↓
4 Variants Compete → Score → Champion Wins
                ↓
Delta > 5% + Burn < 1 → Evolve → Kaggle Pipeline
```

### Fault Tolerance
```
External Call → Circuit Breaker → Execute or Fallback
              ↓
         Open/Closed/Half-Open
```

### FinOps Flow
```
Request → Estimate Cost → Check Margin → Tag Resources → Bill Tenant
```

## Philosophy

> **"Self-funding algorithmic coliseum that breeds champions while never breaking SLO"**

Every design decision prioritizes:
1. **Reliability** - Never lose data, never break SLO
2. **Cost Control** - Forecast and gate before execution
3. **Evolution** - Automatically improve via competition
4. **Observability** - Full visibility into operations
5. **Security** - PII redaction, secure by default

---

**Ready to compete?** Start with the 3 test commands above.

For full details, see `IMPLEMENTATION.md`.
