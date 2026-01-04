# Lab-Verse Monitoring System - Quick Reference Card

## 🚀 Essential Commands

### Deployment
```bash
# Complete deployment
./deploy.sh

# Start services
docker-compose -f docker-compose.production.yml up -d

# Stop services
docker-compose -f docker-compose.production.yml down

# Restart specific service
docker-compose -f docker-compose.production.yml restart api

# View logs
docker-compose -f docker-compose.production.yml logs -f

# Check status
docker-compose -f docker-compose.production.yml ps
```

### Verification
```bash
# Run full system verification
python3 verify_system.py

# Check health
curl http://localhost/health | jq

# Check integrations
curl http://localhost/health/integrations | jq

# Test dashboard
curl http://localhost/api/dashboard/summary | jq
```

### Monitoring
```bash
# Follow all logs
docker-compose -f docker-compose.production.yml logs -f

# Follow API logs
docker-compose -f docker-compose.production.yml logs -f api

# Watch webhook events
docker-compose -f docker-compose.production.yml logs -f api | grep webhook

# Check Redis queue
docker-compose -f docker-compose.production.yml exec redis redis-cli
> LRANGE hubspot:events 0 9
```

---

## 🔗 Access URLs

```
Web Dashboard:       https://localhost
API Documentation:   http://localhost/docs
Grafana:            http://localhost/monitoring/
Prometheus:         http://localhost:9090
```

---

## 🔌 Platform URLs

```
Grafana:            https://somoleli.grafana.net
Hugging Face:       https://huggingface.co/Papimashala
DataDog:            https://app.datadoghq.eu
HubSpot:            https://app-eu1.hubspot.com
Confluence:         https://lab-verse.atlassian.net
ClickUp:            https://app.clickup.com
CodeRabbit:         https://app.coderabbit.ai
```

---

## 📡 Webhook URLs

Replace `yourdomain.com` with your actual domain:

```
Grafana:   https://yourdomain.com/webhooks/grafana
HubSpot:   https://yourdomain.com/webhooks/hubspot
ClickUp:   https://yourdomain.com/webhooks/clickup
DataDog:   https://yourdomain.com/webhooks/datadog
GitHub:    https://yourdomain.com/webhooks/github
```

---

## 🔑 Environment Variables (Required)

```bash
# AI Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Security
JWT_SECRET=<48-char-secret>
POSTGRES_PASSWORD=<secure-password>

# Platform Keys
GRAFANA_API_KEY=...
HUGGINGFACE_TOKEN=hf_...
DATADOG_API_KEY=...
DATADOG_APP_KEY=...
HUBSPOT_ACCESS_TOKEN=...
CONFLUENCE_API_TOKEN=...
CLICKUP_API_TOKEN=...
CODERABBIT_API_KEY=...
```

---

## 🧪 Testing Commands

```bash
# System verification
python3 verify_system.py

# Test health
curl http://localhost/health

# Test integration
curl http://localhost/api/grafana/dashboards | jq

# Test webhook
curl -X POST http://localhost/webhooks/hubspot \
  -H "Content-Type: application/json" \
  -d '{"subscriptionType":"test"}'

# Trigger sync
curl -X POST http://localhost/api/sync \
  -H "Content-Type: application/json" \
  -d '{"platforms":[]}'
```

---

## 🔧 Troubleshooting

### Service won't start
```bash
docker-compose -f docker-compose.production.yml logs <service>
docker-compose -f docker-compose.production.yml restart <service>
```

### Integration failing
```bash
curl http://localhost/health/integrations | jq .integrations.<platform>
cat .env | grep <PLATFORM>_API_KEY
```

### Database issues
```bash
docker-compose -f docker-compose.production.yml exec postgres psql -U labverse
```

### Redis issues
```bash
docker-compose -f docker-compose.production.yml exec redis redis-cli ping
```

---

## 🔄 Common Operations

### Update configuration
```bash
nano .env
docker-compose -f docker-compose.production.yml restart api
```

### Backup database
```bash
docker-compose -f docker-compose.production.yml exec postgres \
  pg_dump -U labverse labverse > backup_$(date +%Y%m%d).sql
```

### Restore database
```bash
cat backup_20250104.sql | \
  docker-compose -f docker-compose.production.yml exec -T postgres \
  psql -U labverse labverse
```

### View container stats
```bash
docker stats
```

### Clean up
```bash
docker-compose -f docker-compose.production.yml down -v
docker system prune -a
```

---

## 📊 Key Metrics

| Metric              | Target     | Command                                    |
|---------------------|------------|-------------------------------------------|
| Response Time       | < 200ms    | `curl -w "%{time_total}" http://localhost/health` |
| Uptime              | 99.9%      | Check Grafana dashboard                   |
| Error Rate          | < 1%       | Check logs and Prometheus                 |
| Integration Health  | All Healthy| `curl http://localhost/health/integrations` |

---

## 🆘 Emergency Procedures

### System not responding
```bash
# 1. Check all services
docker-compose -f docker-compose.production.yml ps

# 2. Restart everything
docker-compose -f docker-compose.production.yml restart

# 3. If still failing, full restart
docker-compose -f docker-compose.production.yml down
docker-compose -f docker-compose.production.yml up -d
```

### Database corruption
```bash
# 1. Stop services
docker-compose -f docker-compose.production.yml stop api orchestrator

# 2. Restore from backup
cat backup_latest.sql | \
  docker-compose -f docker-compose.production.yml exec -T postgres \
  psql -U labverse labverse

# 3. Restart services
docker-compose -f docker-compose.production.yml start api orchestrator
```

### Out of disk space
```bash
# Clean Docker
docker system prune -a -f

# Clean logs
docker-compose -f docker-compose.production.yml exec api \
  find /app/logs -type f -mtime +7 -delete
```

---

## 📞 Support Contacts

```
GitHub Issues:  https://github.com/deedk822-lang/The-lab-verse-monitoring-/issues
Documentation:  http://localhost/docs
Logs:          docker-compose logs
```

---

## ✅ Pre-Deployment Checklist

- [ ] `.env` file configured with all keys
- [ ] SSL certificates installed (production)
- [ ] DNS configured (production)
- [ ] Webhooks configured in all platforms
- [ ] Health checks passing
- [ ] Integration tests passing
- [ ] Backup strategy in place
- [ ] Monitoring dashboards accessible
- [ ] Team trained on system

---

**Save this card for quick reference!**

Print this page and keep it handy for daily operations.