#!/bin/bash
set -e

echo "🚀 PR Fix Agent - Production Deployment"
echo "========================================"
echo ""

# Check requirements
echo "📋 Checking requirements..."

command -v docker >/dev/null 2>&1 || { echo "❌ Docker not found. Install from https://docker.com"; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo "❌ Docker Compose not found"; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "❌ Python 3 not found"; exit 1; }

echo "✅ All requirements met"
echo ""

# Generate secrets
echo "🔐 Generating secrets..."

if [ ! -f .env ]; then
    cat > .env <<EOF
# Database
DB_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)

# Redis
REDIS_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)

# JWT
JWT_SECRET_KEY=$(openssl rand -base64 32)

# HuggingFace (optional - leave empty to use Ollama only)
HF_API_TOKEN=

# Vault (optional)
VAULT_ENABLED=false
VAULT_ADDR=http://localhost:8200
VAULT_TOKEN=

# Grafana
GRAFANA_PASSWORD=admin
EOF
    echo "✅ Created .env with random passwords"
else
    echo "⚠️  .env already exists, skipping"
fi

# Generate TLS certificates
echo "🔒 Generating TLS certificates..."

mkdir -p certs

if [ ! -f certs/ca.key ]; then
    # CA
    openssl genrsa -out certs/ca.key 4096
    openssl req -new -x509 -days 3650 -key certs/ca.key -out certs/ca.crt \
        -subj "/C=US/ST=CA/L=SF/O=PR-Fix-Agent/CN=ca"

    # Server cert
    openssl genrsa -out certs/server.key 4096
    openssl req -new -key certs/server.key -out certs/server.csr \
        -subj "/C=US/ST=CA/L=SF/O=PR-Fix-Agent/CN=postgres"
    openssl x509 -req -days 365 -in certs/server.csr -CA certs/ca.crt -CAkey certs/ca.key \
        -CAcreateserial -out certs/server.crt

    chmod 600 certs/server.key

    echo "✅ Generated TLS certificates"
else
    echo "⚠️  Certificates already exist, skipping"
fi

# Create directories
echo "📁 Creating directories..."
mkdir -p logs analysis-results

# Create Prometheus config
if [ ! -f prometheus.yml ]; then
    cat > prometheus.yml <<'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'pr-fix-agent'
    static_configs:
      - targets: ['api:8000']
    metrics_path: '/metrics'
EOF
    echo "✅ Created prometheus.yml"
fi

# Pull Ollama models
echo "🤖 Setting up Ollama models..."
echo "Note: This will download ~2GB of models"
read -p "Download models now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    docker-compose up -d ollama
    sleep 5

    echo "Pulling qwen2.5-coder:1.5b..."
    docker exec pr-fix-ollama ollama pull qwen2.5-coder:1.5b

    echo "Pulling deepseek-r1:1.5b..."
    docker exec pr-fix-ollama ollama pull deepseek-r1:1.5b

    echo "✅ Models downloaded"
fi

# Start services
echo ""
echo "🎯 Starting services..."
docker-compose up -d

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 10

# Health check
echo "🏥 Health check..."
for i in {1..30}; do
    if curl -sf http://localhost:8000/healthz > /dev/null 2>&1; then
        echo "✅ API is healthy"
        break
    fi
    echo "Waiting... ($i/30)"
    sleep 2
done

# Show status
echo ""
echo "📊 Service Status:"
echo "=================="
docker-compose ps

echo ""
echo "✅ Deployment Complete!"
echo ""
echo "🌐 Access Points:"
echo "  API:        http://localhost:8000"
echo "  Health:     http://localhost:8000/healthz"
echo "  Docs:       http://localhost:8000/docs"
echo "  Metrics:    http://localhost:8000/metrics"
echo "  Prometheus: http://localhost:9090"
echo "  Grafana:    http://localhost:3000 (admin/admin)"
echo ""
echo "📝 Quick Start:"
echo "  1. Test the orchestrator:"
echo "     python3 orchestrator_production.py review --findings analysis-results/bandit.txt --limit 5"
echo ""
echo "  2. View logs:"
echo "     docker-compose logs -f api"
echo ""
echo "  3. Stop services:"
echo "     docker-compose down"
echo ""
echo "🔍 Troubleshooting:"
echo "  - View API logs: docker-compose logs api"
echo "  - Check health: curl http://localhost:8000/healthz"
echo "  - Restart: docker-compose restart api"
echo ""
