# Deployment Checklist

**Last Updated:** October 18, 2025

## Pre-Deployment Checklist

### Environment Configuration
- [ ] `.env.local` created from `.env.example`
- [ ] All API keys configured (at least one AI provider)
- [ ] JWT_SECRET generated (min 32 characters)
- [ ] Redis URL configured correctly
- [ ] Database credentials set
- [ ] Slack webhook configured (optional)

### Validation
- [ ] Environment validation passed: `bash scripts/validate-env.sh`
- [ ] Docker Compose validation passed: `bash scripts/validate-docker.sh`
- [ ] Makefile syntax valid: `make help`
- [ ] No merge conflicts: `git status`

### Dependencies
- [ ] Python dependencies installed: `pip install -r requirements.txt`
- [ ] Node.js dependencies installed: `npm install`
- [ ] TypeScript projects built (if applicable)
  - [ ] `cd src/cardinality-guardian && npm install && npm run build`
  - [ ] `cd src/scout-monetization && npm install && npm run build`
  - [ ] `cd lapverse-core && npm install && npm run build`

### Infrastructure
- [ ] Docker daemon running
- [ ] Docker Compose available
- [ ] Sufficient disk space (10GB+ recommended)
- [ ] Required ports available (3000, 8084, 3001, 9090, 9093, 6379)

## Deployment Steps

### 1. Build Images
```bash
docker-compose build --parallel
```
- [ ] All images built successfully
- [ ] No build errors in logs

### 2. Start Infrastructure Services
```bash
docker-compose up -d redis postgres
```
- [ ] Redis started
- [ ] PostgreSQL started
- [ ] Services healthy (wait 30 seconds)

### 3. Start Monitoring Services
```bash
docker-compose up -d prometheus grafana alertmanager
```
- [ ] Prometheus started
- [ ] Grafana started
- [ ] AlertManager started

### 4. Start Application Services
```bash
docker-compose up -d kimi-project-manager app
```
- [ ] Kimi AI Manager started
- [ ] LapVerse Core started
- [ ] Services responding to health checks

### 5. Verify Deployment
```bash
bash scripts/health-check.sh
```
- [ ] All health checks passing
- [ ] No error logs in `docker-compose logs`

## Post-Deployment Verification

### Service Access
- [ ] Kimi Dashboard accessible: http://localhost:8084/dashboard
- [ ] Grafana accessible: http://localhost:3001 (admin/admin123)
- [ ] Prometheus accessible: http://localhost:9090
- [ ] API endpoints responding: http://localhost:3000/api/v2/health

### Functionality Tests
- [ ] AI analysis working (check Kimi dashboard)
- [ ] Metrics being collected (check Prometheus)
- [ ] Dashboards displaying data (check Grafana)
- [ ] Alerts configured (check AlertManager)

### CLI Tools
- [ ] `./kimi-cli status` working
- [ ] `./kimi-cli checkin` accessible
- [ ] `make` commands functional

## Troubleshooting

### Service Won't Start
1. Check logs: `docker-compose logs <service-name>`
2. Verify environment: `bash scripts/validate-env.sh`
3. Check ports: `netstat -tulpn | grep <port>`
4. Restart service: `docker-compose restart <service-name>`

### Health Checks Failing
1. Wait 2-3 minutes for initialization
2. Check service logs for errors
3. Verify network connectivity between containers
4. Check API keys are valid

### Build Failures
1. Clear Docker cache: `docker-compose build --no-cache`
2. Check Dockerfile syntax
3. Verify base images are accessible
4. Check disk space

## Rollback Plan

If deployment fails:

```bash
# Stop all services
docker-compose down

# Restore from backups
for backup in *.backup.*; do
    original="${backup%.backup.*}"
    cp "$backup" "$original"
done

# Restart with previous configuration
docker-compose up -d
```

## Security Checklist

- [ ] No secrets in git history
- [ ] `.env.local` in `.gitignore`
- [ ] JWT secret is strong (32+ characters)
- [ ] Database passwords changed from defaults
- [ ] TLS enabled for production (if applicable)
- [ ] Firewall rules configured
- [ ] Only required ports exposed

## Monitoring Setup

- [ ] Grafana datasources configured
- [ ] Dashboards imported
- [ ] Alert rules configured
- [ ] Notification channels set up
- [ ] Log aggregation configured

## Documentation

- [ ] Team notified of deployment
- [ ] Runbook updated with any changes
- [ ] Known issues documented
- [ ] Contact information verified

## Sign-off

- [ ] Deployment tested in staging
- [ ] All checklist items completed
- [ ] Stakeholders approved
- [ ] Deployment window scheduled

**Deployed by:** _________________  
**Date:** _________________  
**Approved by:** _________________  