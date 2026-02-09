# PR Fix Agent - Production Deployment Guide

## Quick Start

```bash
# 1. Clone and enter repository
git clone https://github.com/deedk822-lang/The-lab-verse-monitoring-.git
cd The-lab-verse-monitoring-

# 2. Copy environment file
cp .env.production .env
# Edit .env with your values

# 3. Start all services
docker-compose -f docker-compose.prod.yml up -d

# 4. Wait for services to start
sleep 30

# 5. Verify deployment
curl http://localhost:8000/health
curl http://localhost:8000/metrics
```

## Services

| Service | URL | Description |
|---------|-----|-------------|
| API | http://localhost:8000 | PR Fix Agent API |
| Prometheus | http://localhost:9090 | Metrics collection |
| Grafana | http://localhost:3000 | Dashboards (admin/admin) |
| Ollama | http://localhost:11434 | LLM server |

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/metrics` | GET | Prometheus metrics |
| `/api/v1/fix` | POST | Apply code fix |

## Example API Call

```bash
curl -X POST http://localhost:8000/api/v1/fix \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "src/app.py",
    "issue_description": "Fix type error",
    "severity": "high"
  }'
```

## Monitoring

Access Grafana at http://localhost:3000 (login: admin/admin)

Dashboards:
- PR Fix Agent - Production metrics
- Prometheus - System metrics

## Logs

```bash
# View all logs
docker-compose -f docker-compose.prod.yml logs -f

# View specific service
docker-compose -f docker-compose.prod.yml logs -f api
```

## Troubleshooting

```bash
# Check service status
docker-compose -f docker-compose.prod.yml ps

# Restart services
docker-compose -f docker-compose.prod.yml restart

# Reset everything
docker-compose -f docker-compose.prod.yml down -v
docker-compose -f docker-compose.prod.yml up -d
```
