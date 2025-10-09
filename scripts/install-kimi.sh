#!/bin/bash
# scripts/install-kimi.sh
# Installation script for Kimi Instruct AI Project Manager

set -e

echo "🤖 Installing Kimi Instruct AI Project Manager..."
echo "===================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if OpenAI API key is set (optional but recommended)
if [ -z "$OPENAI_API_KEY" ]; then
    echo -e "${YELLOW}⚠️  OPENAI_API_KEY environment variable is not set${NC}"
    echo -e "   Kimi will work without it, but AI features will be limited"
    echo -e "   To set it: export OPENAI_API_KEY='your-key-here'${NC}"
else
    echo -e "${GREEN}✅ OpenAI API key found${NC}"
fi

# Create necessary directories
echo -e "${BLUE}📁 Creating directories...${NC}"
mkdir -p kimi_workspace
mkdir -p logs

# Set permissions
chmod 755 kimi_workspace
chmod 755 logs

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed. Please install Docker first.${NC}"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}❌ Docker Compose is not installed. Please install Docker Compose first.${NC}"
    exit 1
fi

# Build Kimi Docker image
echo -e "${BLUE}🏗️  Building Kimi Docker image...${NC}"
if docker build -f Dockerfile.kimi -t labverse/kimi-manager:latest .; then
    echo -e "${GREEN}✅ Kimi Docker image built successfully${NC}"
else
    echo -e "${RED}❌ Failed to build Kimi Docker image${NC}"
    exit 1
fi

# Check if monitoring network exists
echo -e "${BLUE}🔗 Checking for monitoring network...${NC}"
if ! docker network ls | grep -q "monitoring"; then
    echo -e "${YELLOW}📡 Creating monitoring network...${NC}"
    docker network create monitoring
else
    echo -e "${GREEN}✅ Monitoring network exists${NC}"
fi

# Update main docker-compose.yml to include Kimi service
echo -e "${BLUE}🔧 Updating docker-compose.yml...${NC}"

# Check if kimi service already exists in docker-compose.yml
if grep -q "kimi-project-manager:" docker-compose.yml; then
    echo -e "${YELLOW}⚠️  Kimi service already exists in docker-compose.yml${NC}"
else
    echo -e "${BLUE}➕ Adding Kimi service to docker-compose.yml...${NC}"
    
    # Add Kimi service to the main docker-compose.yml
    cat >> docker-compose.yml << 'EOF'

  # Kimi Instruct AI Project Manager
  kimi-project-manager:
    build:
      context: .
      dockerfile: Dockerfile.kimi
    container_name: labverse_kimi_manager
    restart: unless-stopped
    ports:
      - "8084:8084"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY:-}
      - PROMETHEUS_URL=http://prometheus:9090
      - GRAFANA_URL=http://grafana:3000
      - PROJECT_ID=the-lab-verse-monitoring
      - INITIAL_BUDGET=50000
      - ESTIMATED_DAYS=90
      - SLACK_WEBHOOK_URL=${SLACK_WEBHOOK_URL:-}
      - KIMI_HOST=0.0.0.0
      - KIMI_PORT=8084
    networks:
      - monitoring
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8084/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 45s
    depends_on:
      - prometheus
      - grafana
    volumes:
      - ./kimi_workspace:/app/workspace
      - ./logs:/app/logs
      - ./config/kimi_instruct.json:/app/config/kimi_instruct.json:ro
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.kimi.rule=Host(`kimi.localhost`)"
      - "traefik.http.routers.kimi.entrypoints=web"
      - "traefik.http.services.kimi.loadbalancer.server.port=8084"
EOF
    
    echo -e "${GREEN}✅ Kimi service added to docker-compose.yml${NC}"
fi

# Add Prometheus scrape config for Kimi
echo -e "${BLUE}📊 Updating Prometheus configuration...${NC}"

if [ -f "prometheus/prometheus.yml" ]; then
    if ! grep -q "kimi-project-manager" prometheus/prometheus.yml; then
        echo -e "${BLUE}➕ Adding Kimi to Prometheus scrape targets...${NC}"
        
        # Add Kimi scrape job to prometheus.yml
        cat >> prometheus/prometheus.yml << 'EOF'

  - job_name: 'kimi-project-manager'
    static_configs:
      - targets: ['kimi-project-manager:8084']
    metrics_path: '/metrics'
    scrape_interval: 30s
EOF
        echo -e "${GREEN}✅ Kimi added to Prometheus configuration${NC}"
    else
        echo -e "${YELLOW}⚠️  Kimi already configured in Prometheus${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  prometheus/prometheus.yml not found, skipping Prometheus integration${NC}"
fi

# Create environment file template if it doesn't exist
if [ ! -f ".env" ]; then
    echo -e "${BLUE}📝 Creating .env template...${NC}"
    cat > .env << 'EOF'
# Kimi Instruct Configuration
# OPENAI_API_KEY=your-openai-key-here
# SLACK_WEBHOOK_URL=your-slack-webhook-url

# Project Settings
PROJECT_NAME=the-lab-verse-monitoring
INITIAL_BUDGET=50000
ESTIMATED_DAYS=90

# Monitoring URLs (usually don't need to change)
PROMETHEUS_URL=http://prometheus:9090
GRAFANA_URL=http://grafana:3000
KIMI_URL=http://kimi-project-manager:8084
EOF
    echo -e "${GREEN}✅ .env template created${NC}"
fi

# Test build
echo -e "${BLUE}🧪 Testing Kimi service...${NC}"
if docker run --rm labverse/kimi-manager:latest python -c "from src.kimi_instruct import KimiInstruct; print('✅ Kimi import successful')"; then
    echo -e "${GREEN}✅ Kimi service test passed${NC}"
else
    echo -e "${RED}❌ Kimi service test failed${NC}"
    exit 1
fi

# Create helper scripts
echo -e "${BLUE}📜 Creating helper scripts...${NC}"

# Create kimi CLI script
cat > kimi-cli << 'EOF'
#!/bin/bash
# Kimi CLI wrapper script
docker run --rm -it \
    --network="$(basename $(pwd))_monitoring" \
    -v "$(pwd)/config:/app/config:ro" \
    -v "$(pwd)/kimi_workspace:/app/workspace" \
    -e OPENAI_API_KEY="${OPENAI_API_KEY:-}" \
    labverse/kimi-manager:latest \
    python -m src.kimi_instruct.cli "$@"
EOF

chmod +x kimi-cli
echo -e "${GREEN}✅ Created kimi-cli script${NC}"

# Create status check script
cat > check-kimi << 'EOF'
#!/bin/bash
# Quick Kimi status check
echo "🤖 Kimi Instruct Status Check"
echo "=============================="

if curl -s http://localhost:8084/health > /dev/null 2>&1; then
    echo "✅ Kimi service is running"
    echo "📊 Dashboard: http://localhost:8084/dashboard"
    echo "🔍 Status: http://localhost:8084/status"
    echo "📋 Tasks: http://localhost:8084/tasks"
else
    echo "❌ Kimi service is not responding"
    echo "Try: docker-compose up -d kimi-project-manager"
fi
EOF

chmod +x check-kimi
echo -e "${GREEN}✅ Created check-kimi script${NC}"

# Final success message
echo ""
echo -e "${GREEN}🎉 Kimi Instruct installation completed successfully!${NC}"
echo ""
echo -e "${BLUE}🚀 Next steps:${NC}"
echo -e "1. Set your OpenAI API key: ${YELLOW}export OPENAI_API_KEY='your-key-here'${NC}"
echo -e "2. Start the stack: ${YELLOW}docker-compose up -d${NC}"
echo -e "3. Access Kimi dashboard: ${YELLOW}http://localhost:8084/dashboard${NC}"
echo -e "4. Use CLI: ${YELLOW}./kimi-cli status${NC}"
echo -e "5. Check status: ${YELLOW}./check-kimi${NC}"
echo ""
echo -e "${BLUE}📚 Available endpoints:${NC}"
echo -e "  • Dashboard: ${YELLOW}http://localhost:8084/dashboard${NC}"
echo -e "  • API Status: ${YELLOW}http://localhost:8084/status${NC}"
echo -e "  • Health Check: ${YELLOW}http://localhost:8084/health${NC}"
echo -e "  • Metrics: ${YELLOW}http://localhost:8084/metrics${NC}"
echo ""
echo -e "${GREEN}🎯 Your monitoring stack now has an AI project manager!${NC}"
echo -e "${BLUE}Kimi will help manage your entire monitoring project with AI intelligence.${NC}"
echo ""
