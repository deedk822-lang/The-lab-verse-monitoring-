# 🚀 ECS Deployment Guide

This guide provides concise instructions for deploying the VAAL AI Empire monitoring stack on an Alibaba Cloud ECS instance.

## 📋 Quick Deployment Steps

### 1. SSH into your ECS instance
```bash
ssh -i your-key.pem ubuntu@YOUR_ECS_IP
```

### 2. Run setup
Download and run the production installation script:
```bash
curl -fsSL https://raw.githubusercontent.com/deedk822-lang/The-lab-verse-monitoring-/main/install.sh | sudo bash
```

### 3. Configure Grafana Cloud credentials (Optional)
If you are using Grafana Cloud for monitoring, configure your credentials in the `.env` file:
```bash
nano .env
```

Add the following variables:
```env
# Grafana Cloud Configuration
GRAFANA_CLOUD_PROM_URL="https://prometheus-us-central1.grafana.net/api/prom/push"
GRAFANA_CLOUD_PROM_USER="your-user-id"
GRAFANA_CLOUD_API_KEY="glc_your_api_key"
```

### 4. Start services
Ensure all services are running:
```bash
docker-compose up -d
```

## 📊 Verification
Once deployed, you can verify the status of your services:
```bash
vaal-dashboard
```

Or check the health endpoint:
```bash
curl http://localhost:8000/health
```

## 🔍 Troubleshooting
- **Logs**: Use `vaal-logs` to view application logs.
- **Restart**: Use `vaal-restart` to restart the stack.
- **Emergency**: Use `vaal-emergency-stop` if needed.
