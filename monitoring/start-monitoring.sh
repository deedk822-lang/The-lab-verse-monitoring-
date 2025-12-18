#!/bin/bash
set -e

echo "🚀 Starting Vaal AI Empire Monitoring Stack"
echo "==========================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p monitoring/config/{grafana/{provisioning/{datasources,dashboards},dashboards},rules}

# Set permissions
chmod -R 755 monitoring/

# Start the stack
echo "🐳 Starting Docker containers..."
docker-compose -f docker-compose.monitoring.yml up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to start..."
sleep 10

# Check health
echo "🏥 Checking service health..."
docker-compose -f docker-compose.monitoring.yml ps

echo ""
echo "✅ Monitoring stack is running!"
echo ""
echo "📊 Access URLs:"
echo "  - Grafana:       http://localhost:3001"
echo "  - Prometheus:    http://localhost:9090"
echo "  - Alertmanager:  http://localhost:9093"
echo ""
echo "🔐 Credentials:"
echo "  Username: admin"
echo "  Password: VaalEmpire2025!"
echo ""
echo "📖 Next steps:"
echo "  1. Open Grafana and import dashboard"
echo "  2. Configure Slack webhook for alerts"
echo "  3. Verify metrics at http://localhost:3000/api/metrics"
