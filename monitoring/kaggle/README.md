## 🔌 Kaggle API Integration

### Overview
This monitoring stack includes Grafana with Kaggle dataset integration using the Infinity plugin. The integration enables querying Kaggle's public API for datasets, competitions, and analytics.

### Prerequisites
- Docker & Docker Compose
- Kaggle account with API credentials
- Network access to kaggle.com

### Setup

#### 1. Obtain Kaggle API Credentials
#### 2. Configure Environment Variables
#### 3. Start the Stack
#### 4. Verify Integration
### Dashboard Features

**Kaggle API Integration - Professional Monitoring** dashboard includes:

- 📊 **Live API Queries**: Real-time dataset and competition data
- ❤️ **Health Monitoring**: API connectivity and authentication status
- 🔒 **Security Best Practices**: Credential management and access control guidance
- 🔧 **Troubleshooting Guide**: Common issues and solutions
- 🚀 **Production Roadmap**: Phased deployment checklist

### Security

- ✅ Credentials stored in `secureJsonData` (encrypted at rest)
- ✅ External API access restricted via `allowedHosts`
- ✅ Proxy mode keeps credentials server-side
- ✅ HTTPS-only communication with Kaggle API

### Troubleshooting

**Issue: "401 Unauthorized" errors**
- Verify credentials in `.env` match kaggle.json
- Ensure using API key (not account password)
- Check datasource uses Basic authentication

**Issue: "No data" in panels**
- Run `./scripts/test-kaggle-integration.sh`
- Check Grafana logs: `docker-compose logs grafana`
- Verify network connectivity to kaggle.com

### Production Checklist

- [ ] Migrate credentials to secrets manager (Vault/K8s Secrets)
- [ ] Configure Grafana alerting rules
- [ ] Set up monitoring dashboards backup
- [ ] Implement rate limit monitoring
- [ ] Document runbooks for common failures

### Resources

- [Kaggle API Documentation](https://github.com/Kaggle/kaggle-api)
- [Infinity Plugin Docs](https://grafana.com/grafana/plugins/yesoreyeram-infinity-datasource/)
- [Dashboard in Grafana](http://localhost:3000/d/kaggle-integration)
