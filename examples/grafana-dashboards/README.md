# 🌍 Vaal AI Empire - Production Dashboard

Enterprise-grade Grafana dashboard for monitoring Model Arbitrage AI Gateway.

## Features

- **26 Professional Panels** - Complete observability
- **7 Alert Rules** - Proactive issue detection
- **3 AI Models** - Qwen Orchestrator, DeepSeek SARS, Qwen VL Seer
- **SARS Compliance** - South African tax analysis tracking
- **GDELT Monitoring** - Crisis event detection

## Quick Start

### 1. Import to Grafana

### 2. Configure Data Source

The dashboard expects a Prometheus datasource with:
- **Name**: `Prometheus` or use your datasource UID
- **URL**: Your Prometheus server (e.g., `http://prometheus:9090`)
- **Scrape interval**: 15s

### 3. Deploy Monitoring Stack

## Dashboard Structure

### Sections
1. **Header** - Overview with SLO targets
2. **Gateway KPIs** - Request rate, errors, latency, uptime
3. **Model Arbitrage** - Distribution across AI agents
4. **Performance** - Latency comparison by model
5. **SARS Compliance** - Queue, processing time, rate
6. **GDELT Monitoring** - Data freshness, event tracking
7. **System Health** - Memory, CPU, Redis, alerts
8. **Network** - Traffic analysis
9. **Service Status** - Uptime for all components
10. **Analytics** - HTTP status codes, top endpoints
11. **Alerts Table** - Live alert dashboard
12. **Documentation** - Architecture reference

## Requirements

- Grafana 9.0+
- Prometheus datasource
- Metrics endpoint at `/api/metrics`

## Customization

Edit `prometheus.yml` to match your endpoints:

## Support

- **GitHub Issues**: [Report problems](https://github.com/deedk822-lang/The-lab-verse-monitoring-/issues)
- **Documentation**: [docs.vaalempire.co.za](https://docs.vaalempire.co.za)
- **Status Page**: [status.vaalempire.co.za](https://status.vaalempire.co.za)

## License

MIT - See [LICENSE](../../LICENSE) for details.
