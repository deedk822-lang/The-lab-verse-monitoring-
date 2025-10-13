# QUICKSTART

## Prerequisites
- Node.js 18+
- Docker (for Redis)
- API keys set in `.env.local` (never commit this file)

Example `.env.local` (place at repo root):
```
QWEN_API_URL=https://your-qwen-endpoint
QWEN_API_KEY=sk-...
KIMI_API_URL=https://your-kimi-endpoint
KIMI_API_KEY=sk-...
```

## Start services
```bash
docker run -d -p 6379:6379 redis:7-alpine
```

## Install and run core
```bash
cd lapverse-core
npm install
npm run dev
```

## Smoke the API
```bash
curl -X POST localhost:3000/api/v2/tasks \
  -H "Idempotency-Key: $(uuidgen)" \
  -H "X-Tenant-ID: acme" \
  -H "Content-Type: application/json" \
  -d '{"type":"ANALYSIS","priority":"high","description":"Forecast Q3 revenue","tenant":"acme","platforms":["twitter"],"costCenter":"campaign-9000"}'
```

## Validate AI connectivity
```bash
cd lapverse-core
npx tsx test-ai-connector.ts
```

