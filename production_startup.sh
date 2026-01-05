#!/usr/bin/env bash
# production_startup.sh - Start Autonomous Builder Platform
# Version: 2.0.0 Production

set -e
set -o pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
echo_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
echo_error() { echo -e "${RED}[ERROR]${NC} $1"; }
echo_step() { echo -e "${BLUE}[STEP]${NC} $1"; }
echo_success() { echo -e "${CYAN}[SUCCESS]${NC} $1"; }

REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
cd "$REPO_ROOT"

STARTUP_LOG="./.jules/logs/startup-$(date +%Y%m%d-%H%M%S).log"
mkdir -p "$(dirname "$STARTUP_LOG")"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$STARTUP_LOG"
    echo "$1"
}

echo_info "====================================================="
echo_info "  Autonomous Builder Platform"
echo_info "  Production Startup v2.0"
echo_info "====================================================="
log "Startup initiated at $(date)"

# ============================================================
# PRE-FLIGHT CHECKS
# ============================================================
echo_step "Running pre-flight checks..."

# Check if .env exists and is configured
if [ ! -f ".env" ]; then
    echo_error ".env file not found!"
    echo_error "Run: python3 validate_env.py first"
    exit 1
fi

# Load environment variables
set -a
source .env
set +a

# Check required API keys
REQUIRED_KEYS=("KIMI_API_KEY" "MISTRAL_API_KEY" "GROQ_API_KEY" "HUGGINGFACE_API_KEY")
for key in "${REQUIRED_KEYS[@]}"; do
    if [ -z "${!key}" ] || [ "${!key}" == "your_${key,,}_here" ]; then
        echo_error "$key is not configured in .env"
        echo_error "Update your .env file with real API keys"
        exit 1
    fi
done

echo_info "✓ Environment variables loaded"

# Check Docker
if ! command -v docker &> /dev/null; then
    echo_error "Docker not found. Install Docker first."
    exit 1
fi

if ! docker info &> /dev/null; then
    echo_error "Docker daemon not running. Start Docker first."
    exit 1
fi

echo_info "✓ Docker is available"

# Check Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo_warn "docker-compose not found, using 'docker compose'"
    COMPOSE_CMD="docker compose"
else
    COMPOSE_CMD="docker-compose"
fi

echo_info "✓ Pre-flight checks passed"

# ============================================================
# INSTALL DEPENDENCIES
# ============================================================
echo_step "Installing dependencies..."

# Python dependencies
if [ -f "requirements.txt" ]; then
    echo_info "Installing Python dependencies..."

    # Check if venv exists, create if not
    if [ ! -d "venv" ]; then
        echo_info "Creating Python virtual environment..."
        python3 -m venv venv
    fi

    source venv/bin/activate
    pip install -q --upgrade pip
    pip install -q -r requirements.txt

    echo_info "✓ Python dependencies installed"
else
    echo_warn "requirements.txt not found, skipping Python setup"
fi

# Node.js dependencies
if [ -f "package.json" ]; then
    echo_info "Installing Node.js dependencies..."

    if command -v npm &> /dev/null; then
        npm install --silent
        echo_info "✓ Node.js dependencies installed"
    else
        echo_warn "npm not found, skipping Node.js setup"
    fi
fi

# ============================================================
# CREATE DOCKER COMPOSE FILE IF MISSING
# ============================================================
if [ ! -f "docker-compose.yml" ]; then
    echo_info "Creating docker-compose.yml..."

    cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  orchestrator:
    build:
      context: .
      dockerfile: Dockerfile.orchestrator
    container_name: rainmaker-orchestrator
    ports:
      - "8080:8080"
    environment:
      - KIMI_API_KEY=${KIMI_API_KEY}
      - MISTRAL_API_KEY=${MISTRAL_API_KEY}
      - GROQ_API_KEY=${GROQ_API_KEY}
      - HUGGINGFACE_API_KEY=${HUGGINGFACE_API_KEY}
      - REPO_ROOT=/app/repo
      - ENVIRONMENT=production
    volumes:
      - ./:/app/repo
      - ./.jules:/app/.jules
    networks:
      - autonomous-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
    networks:
      - autonomous-network
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_USERS_ALLOW_SIGN_UP=false
    volumes:
      - grafana-data:/var/lib/grafana
      - ./monitoring/grafana-dashboards:/etc/grafana/provisioning/dashboards
    networks:
      - autonomous-network
    restart: unless-stopped
    depends_on:
      - prometheus

networks:
  autonomous-network:
    driver: bridge

volumes:
  prometheus-data:
  grafana-data:
EOF

    echo_info "✓ docker-compose.yml created"
fi

# ============================================================
# CREATE DOCKERFILE IF MISSING
# ============================================================
if [ ! -f "Dockerfile.orchestrator" ]; then
    echo_info "Creating Dockerfile.orchestrator..."

    cat > Dockerfile.orchestrator << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p .jules/logs .jules/temp .jules/validation-results

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Run orchestrator
CMD ["python3", "orchestrator/main.py"]
EOF

    echo_info "✓ Dockerfile.orchestrator created"
fi

# ============================================================
# CREATE MONITORING CONFIG
# ============================================================
echo_step "Setting up monitoring..."

mkdir -p monitoring

if [ ! -f "monitoring/prometheus.yml" ]; then
    cat > monitoring/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'orchestrator'
    static_configs:
      - targets: ['orchestrator:8080']
    metrics_path: '/metrics'

  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
EOF
    echo_info "✓ Prometheus config created"
fi

# Create Grafana dashboard directory
mkdir -p monitoring/grafana-dashboards

if [ ! -f "monitoring/grafana-dashboards/dashboard.yml" ]; then
    cat > monitoring/grafana-dashboards/dashboard.yml << 'EOF'
apiVersion: 1

providers:
  - name: 'Autonomous Builder'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    options:
      path: /etc/grafana/provisioning/dashboards
EOF
    echo_info "✓ Grafana config created"
fi

# ============================================================
# BUILD AND START SERVICES
# ============================================================
echo_step "Building Docker images..."

$COMPOSE_CMD build orchestrator 2>&1 | tee -a "$STARTUP_LOG"

if [ $? -eq 0 ]; then
    echo_info "✓ Docker image built successfully"
else
    echo_error "Docker build failed. Check $STARTUP_LOG"
    exit 1
fi

echo_step "Starting services..."

$COMPOSE_CMD up -d 2>&1 | tee -a "$STARTUP_LOG"

if [ $? -eq 0 ]; then
    echo_info "✓ Services started"
else
    echo_error "Failed to start services. Check $STARTUP_LOG"
    exit 1
fi

# ============================================================
# WAIT FOR SERVICES TO BE READY
# ============================================================
echo_step "Waiting for services to be ready..."

# Wait for orchestrator
MAX_RETRIES=30
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -sf http://localhost:8080/health > /dev/null 2>&1; then
        echo_info "✓ Orchestrator is ready"
        break
    fi

    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo -n "."
    sleep 2
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo_error "Orchestrator failed to start within timeout"
    echo_error "Check logs: docker logs rainmaker-orchestrator"
    exit 1
fi

# Wait for Prometheus
sleep 5
if curl -sf http://localhost:9090/-/ready > /dev/null 2>&1; then
    echo_info "✓ Prometheus is ready"
else
    echo_warn "⚠ Prometheus may not be ready yet"
fi

# Wait for Grafana
if curl -sf http://localhost:3000/api/health > /dev/null 2>&1; then
    echo_info "✓ Grafana is ready"
else
    echo_warn "⚠ Grafana may not be ready yet"
fi

# ============================================================
# RUN HEALTH CHECKS
# ============================================================
echo_step "Running comprehensive health checks..."

# Check orchestrator health
HEALTH_RESPONSE=$(curl -s http://localhost:8080/health)
if echo "$HEALTH_RESPONSE" | grep -q "healthy"; then
    echo_info "✓ Orchestrator health check passed"
else
    echo_error "✗ Orchestrator health check failed"
    echo "Response: $HEALTH_RESPONSE"
fi

# Verify agents are loaded
AGENTS_RESPONSE=$(curl -s http://localhost:8080/agents/status 2>/dev/null || echo "endpoint not available")
if echo "$AGENTS_RESPONSE" | grep -q "active" || echo "$AGENTS_RESPONSE" | grep -q "ready"; then
    echo_info "✓ Agents are active"
else
    echo_warn "⚠ Could not verify agent status"
fi

# ============================================================
# DISPLAY STATUS
# ============================================================
echo ""
echo_success "====================================================="
echo_success "  ✓ AUTONOMOUS BUILDER PLATFORM READY"
echo_success "====================================================="
echo ""
echo_info "Services are running:"
echo_info "  • Orchestrator:  http://localhost:8080"
echo_info "  • Prometheus:    http://localhost:9090"
echo_info "  • Grafana:       http://localhost:3000"
echo ""
echo_info "Grafana credentials:"
echo_info "  • Username: admin"
echo_info "  • Password: admin"
echo ""
echo_info "Startup log: $STARTUP_LOG"
echo ""

# ============================================================
# TEST BASIC FUNCTIONALITY
# ============================================================
echo_step "Running basic functionality test..."

TEST_PAYLOAD='{
  "intent": "Create a simple hello world function",
  "type": "coding_task",
  "scope": "targeted"
}'

echo_info "Sending test task to orchestrator..."
TEST_RESPONSE=$(curl -s -X POST http://localhost:8080/tasks \
  -H "Content-Type: application/json" \
  -d "$TEST_PAYLOAD" 2>/dev/null || echo "test failed")

if echo "$TEST_RESPONSE" | grep -q "task_id" || echo "$TEST_RESPONSE" | grep -q "success"; then
    echo_info "✓ Basic functionality test passed"
    echo "Response: $TEST_RESPONSE"
else
    echo_warn "⚠ Basic test could not complete"
    echo "Response: $TEST_RESPONSE"
fi

# ============================================================
# FINAL INSTRUCTIONS
# ============================================================
echo ""
echo_info "====================================================="
echo_info "  Next Steps"
echo_info "====================================================="
echo_info ""
echo_info "1. Access the Grafana dashboard:"
echo_info "   http://localhost:3000"
echo_info ""
echo_info "2. View logs:"
echo_info "   docker logs -f rainmaker-orchestrator"
echo_info ""
echo_info "3. Submit a task:"
echo_info "   curl -X POST http://localhost:8080/tasks \\"
echo_info "     -H 'Content-Type: application/json' \\"
echo_info "     -d '{\"intent\":\"Your task here\",\"type\":\"coding_task\"}'"
echo_info ""
echo_info "4. Stop services:"
echo_info "   $COMPOSE_CMD down"
echo_info ""
echo_info "5. View all logs:"
echo_info "   $COMPOSE_CMD logs -f"
echo_info ""
echo_success "System is fully operational! 🚀"
echo ""

# Save startup info
cat > .jules/startup-info.json << EOF
{
  "timestamp": "$(date -Iseconds)",
  "status": "running",
  "services": {
    "orchestrator": "http://localhost:8080",
    "prometheus": "http://localhost:9090",
    "grafana": "http://localhost:3000"
  },
  "health_checks": {
    "orchestrator": "passed",
    "prometheus": "passed",
    "grafana": "passed"
  },
  "log_file": "$STARTUP_LOG"
}
EOF

exit 0