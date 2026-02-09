#!/bin/bash
# The Lab Verse Monitoring Stack - One-Command Production Setup
# From zero to fully operational AI-powered monitoring in minutes

set -e

# Colors and styling
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# ASCII Art Header
print_header() {
    echo -e "${PURPLE}${BOLD}"
    cat << 'EOF'
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║         🚀 THE LAB VERSE MONITORING STACK 🚀                ║
║                                                               ║
║              AI-Powered Infrastructure Manager                ║
║                     Production Setup                          ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"
}

log_step() {
    echo -e "\n${BLUE}${BOLD}⏳ STEP $1: $2${NC}"
    echo -e "${BLUE}${BOLD}$3${NC}"
}

log_success() {
    echo -e "${GREEN}${BOLD}✅ $1${NC}"
}

log_error() {
    echo -e "${RED}${BOLD}❌ ERROR: $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}${BOLD}⚠️  WARNING: $1${NC}"
}

log_info() {
    echo -e "${CYAN}ℹ️  $1${NC}"
}

# Check if we're in the right directory
check_directory() {
    if [[ ! -f "README.md" ]] || [[ ! $(grep -q "Lab.*Verse" README.md 2>/dev/null) ]]; then
        log_error "This script must be run from The Lab Verse Monitoring Stack repository root"
        echo "Please run: git clone https://github.com/deedk822-lang/The-lab-verse-monitoring-.git"
        exit 1
    fi
}

# Prerequisites check with installation guidance
check_prerequisites() {
    log_step "1" "CHECKING PREREQUISITES" "Verifying system requirements and dependencies"
    
    local all_good=true
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker not found"
        echo "Install Docker: https://docs.docker.com/get-docker/"
        all_good=false
    else
        log_success "Docker found: $(docker --version | cut -d' ' -f3)"
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose not found"
        echo "Install Docker Compose: https://docs.docker.com/compose/install/"
        all_good=false
    else
        if command -v docker-compose &> /dev/null; then
            log_success "Docker Compose found: $(docker-compose --version | cut -d' ' -f4)"
        else
            log_success "Docker Compose found: $(docker compose version --short)"
        fi
    fi
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 not found"
        echo "Install Python 3.8+: https://www.python.org/downloads/"
        all_good=false
    else
        python_version=$(python3 --version | cut -d' ' -f2)
        log_success "Python found: $python_version"
        
        # Check if version is 3.8+
        python_major=$(echo $python_version | cut -d. -f1)
        python_minor=$(echo $python_version | cut -d. -f2)
        if [[ $python_major -lt 3 ]] || [[ $python_major -eq 3 && $python_minor -lt 8 ]]; then
            log_warning "Python 3.8+ recommended (found $python_version)"
        fi
    fi
    
    # Check Node.js (optional but recommended)
    if command -v node &> /dev/null; then
        node_version=$(node --version)
        log_success "Node.js found: $node_version"
    else
        log_warning "Node.js not found (optional but recommended)"
        log_info "Install from: https://nodejs.org/"
    fi
    
    # Check available disk space (in KB, convert to GB)
    if command -v df &> /dev/null; then
        available_kb=$(df . | awk 'NR==2 {print $4}')
        available_gb=$((available_kb / 1024 / 1024))
        
        if [[ $available_gb -lt 10 ]]; then
            log_warning "Only ${available_gb}GB available (10GB+ recommended)"
        else
            log_success "Disk space: ${available_gb}GB available"
        fi
    fi
    
    # Check Docker daemon
    if ! docker info &> /dev/null; then
        log_error "Docker daemon not running"
        echo "Start Docker daemon first"
        all_good=false
    else
        log_success "Docker daemon running"
    fi
    
    if [[ $all_good != true ]]; then
        log_error "Prerequisites not met. Please install missing components."
        exit 1
    fi
    
    log_success "All prerequisites satisfied!"
}

# Setup files and directories
setup_structure() {
    log_step "2" "SETTING UP PROJECT STRUCTURE" "Creating directories and essential files"
    
    # Create directories
    directories=(
        "config"
        "src/kimi_instruct"
        "data"
        "logs"
        "monitoring/grafana/dashboards"
        "monitoring/grafana/datasources"
        "monitoring/prometheus"
        "static"
        "scripts"
        "nginx"
    )
    
    for dir in "${directories[@]}"; do
        mkdir -p "$dir"
        log_info "Created: $dir"
    done
    
    log_success "Project structure ready!"
}

# Environment setup
setup_environment() {
    log_step "3" "CONFIGURING ENVIRONMENT" "Setting up environment variables and API keys"
    
    # Create .env.local if it doesn't exist
    if [[ ! -f ".env.local" ]]; then
        if [[ -f ".env.example" ]]; then
            cp .env.example .env.local
            log_info "Created .env.local from template"
        else
            log_info "Creating minimal .env.local"
            cat > .env.local << 'EOF'
# The Lab Verse Monitoring Stack - Environment Configuration
NODE_ENV=production
PYTHON_ENV=production
REDIS_PASSWORD=redis123
GRAFANA_ADMIN_PASSWORD=admin123
JWT_SECRET=labverse-jwt-secret-key-production-2024
PROJECT_BUDGET=100000

# Add your AI API keys here:
# OPENAI_API_KEY=sk-your-openai-key
# ANTHROPIC_API_KEY=sk-ant-your-anthropic-key
# DASHSCOPE_API_KEY=sk-your-dashscope-key
# MOONSHOT_API_KEY=sk-your-moonshot-key
EOF
        fi
        
        echo
        log_warning "🔑 API KEYS REQUIRED FOR FULL FUNCTIONALITY"
        log_info "Edit .env.local and add your AI API keys:"
        log_info "  • DashScope (Qwen): https://dashscope.aliyun.com/"
        log_info "  • OpenAI: https://platform.openai.com/api-keys"  
        log_info "  • Anthropic: https://console.anthropic.com/"
        log_info "  • Moonshot AI: https://platform.moonshot.cn/"
        echo
        log_info "The system will work with fallback modes without API keys, but AI features will be limited."
        
        read -p "Do you want to edit .env.local now? [y/N] " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            ${EDITOR:-nano} .env.local
        fi
    else
        log_info ".env.local already exists"
    fi
    
    # Add to gitignore
    if ! grep -q ".env.local" .gitignore 2>/dev/null; then
        echo -e "\n# Environment variables\n.env.local\n.env" >> .gitignore
        log_info "Added .env.local to .gitignore"
    fi
    
    log_success "Environment configured!"
}

# Install dependencies
install_dependencies() {
    log_step "4" "INSTALLING DEPENDENCIES" "Installing Python and Node.js dependencies"
    
    # Python dependencies
    if [[ -f "requirements.txt" ]]; then
        log_info "Installing Python dependencies..."
        
        # Create virtual environment if requested
        if [[ "${USE_VENV:-false}" == "true" ]] && [[ ! -d "venv" ]]; then
            python3 -m venv venv
            source venv/bin/activate
            log_info "Created and activated Python virtual environment"
        fi
        
        python3 -m pip install --upgrade pip
        pip install -r requirements.txt
        log_success "Python dependencies installed"
    fi
    
    # Node.js dependencies
    if [[ -f "package.json" ]] && command -v npm &> /dev/null; then
        log_info "Installing Node.js dependencies..."
        npm install
        log_success "Node.js dependencies installed"
    fi
}

# Create monitoring configurations
create_monitoring_configs() {
    log_step "5" "CREATING MONITORING CONFIGS" "Setting up Prometheus, Grafana, and AlertManager"
    
    # Prometheus configuration
    if [[ ! -f "monitoring/prometheus.yml" ]]; then
        cat > monitoring/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    cluster: 'labverse-production'

rule_files:
  - "alert_rules.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

scrape_configs:
  - job_name: 'kimi-instruct'
    static_configs:
      - targets: ['kimi-project-manager:8084']
    scrape_interval: 10s
    metrics_path: '/metrics'
    
  - job_name: 'lapverse-core'
    static_configs:
      - targets: ['app:3000']
    scrape_interval: 10s
    metrics_path: '/metrics'
    
  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']
    scrape_interval: 15s
    
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
    scrape_interval: 30s
EOF
        log_success "Created Prometheus configuration"
    fi
    
    # Alert rules
    if [[ ! -f "monitoring/alert_rules.yml" ]]; then
        cat > monitoring/alert_rules.yml << 'EOF'
groups:
- name: labverse-alerts
  rules:
  - alert: HighTaskFailureRate
    expr: rate(kimi_tasks_total{status="failed"}[5m]) > 0.1
    for: 2m
    labels:
      severity: warning
    annotations:
      summary: "High task failure rate detected"
      description: "Task failure rate is {{ $value }} per second"
      
  - alert: AIProviderDown
    expr: up{job="kimi-instruct"} == 0
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "Kimi Instruct service is down"
      
  - alert: HighRiskScore
    expr: kimi_project_risk_score > 0.8
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "Project risk score is high: {{ $value }}"
EOF
        log_success "Created alert rules"
    fi
    
    # Grafana datasources
    mkdir -p monitoring/grafana/datasources
    cat > monitoring/grafana/datasources/prometheus.yml << 'EOF'
apiVersion: 1
datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: true
    jsonData:
      timeInterval: "15s"
EOF
    log_success "Created Grafana datasource configuration"
    
    # AlertManager config
    if [[ ! -f "monitoring/alertmanager.yml" ]]; then
        cat > monitoring/alertmanager.yml << 'EOF'
global:
  smtp_smarthost: 'localhost:587'
  smtp_from: 'labverse-alerts@localhost'

route:
  group_by: ['alertname', 'cluster', 'service']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'default'
  routes:
  - match:
      severity: critical
    receiver: 'critical'
    
receivers:
- name: 'default'
  webhook_configs:
  - url: 'http://kimi-project-manager:8084/api/v1/alerts'
    send_resolved: true
    
- name: 'critical'
  webhook_configs:
  - url: 'http://kimi-project-manager:8084/api/v1/alerts/critical'
    send_resolved: true
EOF
        log_success "Created AlertManager configuration"
    fi
}

# Create essential Dockerfiles
create_dockerfiles() {
    log_step "6" "CREATING DOCKER CONFIGURATIONS" "Building container definitions for Kimi service"
    
    # Kimi Dockerfile
    if [[ ! -f "Dockerfile.kimi" ]]; then
        cat > Dockerfile.kimi << 'EOF'
FROM python:3.11-slim

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    gcc \
    g++ \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create app user for security
RUN useradd --create-home --shell /bin/bash --user-group labverse
WORKDIR /app
RUN chown labverse:labverse /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ src/
COPY config/ config/
COPY kimi-cli .

# Create necessary directories with proper permissions
RUN mkdir -p data logs && \
    chown -R labverse:labverse /app

# Switch to non-root user
USER labverse

# Expose port
EXPOSE 8084

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8084/health || exit 1

# Run the service
CMD ["python", "src/kimi_instruct/service.py"]
EOF
        log_success "Created Kimi Dockerfile"
    fi
}

# Start the stack
start_stack() {
    log_step "7" "STARTING THE STACK" "Building images and starting all services"
    
    # Load environment variables
    if [[ -f ".env.local" ]]; then
        set -a  # automatically export all variables
        source .env.local
        set +a
        log_info "Loaded environment from .env.local"
    fi
    
    # Build images
    log_info "Building Docker images..."
    if command -v docker-compose &> /dev/null; then
        docker-compose build --parallel
    else
        docker compose build --parallel
    fi
    
    # Start services in stages for proper dependency handling
    log_info "Starting infrastructure services..."
    if command -v docker-compose &> /dev/null; then
        docker-compose up -d redis postgres
    else
        docker compose up -d redis postgres
    fi
    
    sleep 10
    
    log_info "Starting monitoring services..."
    if command -v docker-compose &> /dev/null; then
        docker-compose up -d prometheus grafana alertmanager node-exporter
    else
        docker compose up -d prometheus grafana alertmanager node-exporter
    fi
    
    sleep 10
    
    log_info "Starting application services..."
    if command -v docker-compose &> /dev/null; then
        docker-compose up -d kimi-project-manager app
    else
        docker compose up -d kimi-project-manager app
    fi
    
    sleep 10
    
    log_info "Starting supporting services..."
    if command -v docker-compose &> /dev/null; then
        docker-compose up -d ollama otel-collector nginx
    else
        docker compose up -d ollama otel-collector nginx
    fi
    
    log_success "All services started!"
}

# Setup Ollama models
setup_ollama_models() {
    log_step "8" "SETTING UP LOCAL AI MODELS" "Downloading Ollama models for zero-cost AI"
    
    # Start Ollama if not running
    if command -v docker-compose &> /dev/null; then
        if ! docker-compose ps ollama | grep -q "Up"; then
            log_info "Starting Ollama service..."
            docker-compose up -d ollama
            sleep 30
        fi
    else
        if ! docker compose ps ollama | grep -q "Up"; then
            log_info "Starting Ollama service..."
            docker compose up -d ollama
            sleep 30
        fi
    fi
    
    # Check if models should be downloaded
    echo
    log_info "Local AI models provide zero-cost intelligence but require 4-8GB download"
    read -p "Download AI models now? (Recommended) [Y/n] " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        log_info "Downloading Qwen2 7B model (faster download)..."
        docker exec labverse-ollama ollama pull qwen2:7b || {
            log_warning "Qwen2 download failed, trying alternative model..."
            docker exec labverse-ollama ollama pull llama3:8b
        }
        
        log_info "Optionally downloading Mixtral 8x7B model (this may take 10-30 minutes)..."
        read -p "Download larger Mixtral model? [y/N] " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            docker exec labverse-ollama ollama pull mixtral:8x7b-instruct || {
                log_warning "Mixtral download failed, continuing with available models"
            }
        fi
        
        log_success "Local AI models ready!"
    else
        log_info "Skipped AI model download. You can run this later:"
        log_info "  docker exec labverse-ollama ollama pull qwen2:7b"
    fi
}

# Verify installation
verify_installation() {
    log_step "9" "VERIFYING INSTALLATION" "Testing all services and connectivity"
    
    log_info "Waiting for services to fully initialize..."
    sleep 45
    
    # Service health checks
    services=(
        "http://localhost:8084/health|🤖 Kimi Instruct AI Manager"
        "http://localhost:3000/health|⚡ LapVerse Core Service"
        "http://localhost:3001/api/health|📊 Grafana Dashboard"
        "http://localhost:9090/-/healthy|📈 Prometheus Metrics"
        "http://localhost:9093/-/healthy|🚨 AlertManager"
    )
    
    echo
    log_info "🏥 HEALTH CHECK RESULTS:"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    all_healthy=true
    
    for service in "${services[@]}"; do
        IFS='|' read -r url name <<< "$service"
        
        if curl -sf --max-time 10 "$url" > /dev/null 2>&1; then
            log_success "$name"
        else
            log_error "$name - Not responding"
            all_healthy=false
        fi
    done
    
    # Test CLI if available
    if [[ -f "kimi-cli" ]]; then
        chmod +x kimi-cli
        log_info "Testing CLI functionality..."
        if python3 kimi-cli status > /dev/null 2>&1; then
            log_success "🖥️  CLI Interface"
        else
            log_warning "🖥️  CLI Interface - Limited functionality"
        fi
    fi
    
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    if $all_healthy; then
        print_success_banner
    else
        echo
        log_warning "Some services are not responding. This might be due to:"
        log_info "  • Services still starting up (wait 2-3 minutes)"
        log_info "  • Missing API keys (add to .env.local)"
        log_info "  • Port conflicts (check with: netstat -tulpn)"
        echo
        log_info "Check logs with: docker-compose logs <service-name>"
        log_info "Restart services with: docker-compose restart"
    fi
}

# Success banner
print_success_banner() {
    echo
    echo -e "${GREEN}${BOLD}"
    cat << 'EOF'
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║                    🎉 INSTALLATION COMPLETE! 🎉              ║
║                                                               ║
║            The Lab Verse Monitoring Stack is LIVE            ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"
    
    echo -e "${CYAN}${BOLD}🌟 YOUR AI-POWERED MONITORING STACK IS READY!${NC}"
    echo
    echo -e "${BLUE}📱 ACCESS POINTS:${NC}"
    echo -e "${GREEN}  🤖 Kimi AI Dashboard:     ${BOLD}http://localhost:8084/dashboard${NC}"
    echo -e "${GREEN}  📊 Grafana Monitoring:    ${BOLD}http://localhost:3001${NC} (admin/admin123)"
    echo -e "${GREEN}  📈 Prometheus Metrics:    ${BOLD}http://localhost:9090${NC}"
    echo -e "${GREEN}  🚨 AlertManager:          ${BOLD}http://localhost:9093${NC}"
    echo -e "${GREEN}  ⚡ LapVerse Core API:     ${BOLD}http://localhost:3000/api/v2${NC}"
    echo
    echo -e "${BLUE}🛠️  QUICK COMMANDS:${NC}"
    echo -e "${YELLOW}  ./kimi-cli status --detailed${NC}                    # Get AI-powered status"
    echo -e "${YELLOW}  ./kimi-cli checkin${NC}                              # Interactive human checkin"
    echo -e "${YELLOW}  ./kimi-cli revenue --target-mrr 25000${NC}           # Revenue optimization"
    echo -e "${YELLOW}  docker-compose logs -f kimi-project-manager${NC}     # View logs"
    echo
    echo -e "${PURPLE}💡 NEXT STEPS:${NC}"
    echo -e "  1. Add your AI API keys to .env.local for full functionality"
    echo -e "  2. Visit the Kimi Dashboard to create your first AI-managed task"
    echo -e "  3. Explore revenue optimization and monitoring dashboards"
    echo -e "  4. Configure notifications and alerts as needed"
    echo
    echo -e "${GREEN}${BOLD}🚀 Your monitoring infrastructure now has an AI project manager!${NC}"
    echo
}

# Main installation function
main() {
    clear
    print_header
    
    echo -e "${BOLD}Welcome to The Lab Verse Monitoring Stack Production Setup!${NC}"
    echo -e "This script will install and configure your AI-powered monitoring infrastructure."
    echo
    
    # Confirmation
    read -p "Ready to begin installation? [Y/n] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Nn]$ ]]; then
        echo "Installation cancelled."
        exit 0
    fi
    
    # Run installation steps
    check_directory
    check_prerequisites
    setup_structure
    setup_environment
    install_dependencies
    create_monitoring_configs
    create_dockerfiles
    start_stack
    
    # Optional: Setup Ollama models
    setup_ollama_models
    
    # Final verification
    verify_installation
}

# Handle command line arguments
case "${1:-install}" in
    "install"|"")
        main
        ;;
    "start")
        log_info "🚀 Starting The Lab Verse Monitoring Stack..."
        if command -v docker-compose &> /dev/null; then
            docker-compose up -d
        else
            docker compose up -d
        fi
        log_success "All services started!"
        ;;
    "stop")
        log_info "🛑 Stopping The Lab Verse Monitoring Stack..."
        if command -v docker-compose &> /dev/null; then
            docker-compose down
        else
            docker compose down
        fi
        log_success "All services stopped!"
        ;;
    "restart")
        log_info "🔄 Restarting The Lab Verse Monitoring Stack..."
        if command -v docker-compose &> /dev/null; then
            docker-compose restart
        else
            docker compose restart
        fi
        log_success "All services restarted!"
        ;;
    "status")
        echo -e "${BLUE}📊 Service Status:${NC}"
        if command -v docker-compose &> /dev/null; then
            docker-compose ps
        else
            docker compose ps
        fi
        ;;
    "logs")
        if [[ -n "$2" ]]; then
            if command -v docker-compose &> /dev/null; then
                docker-compose logs -f "$2"
            else
                docker compose logs -f "$2"
            fi
        else
            if command -v docker-compose &> /dev/null; then
                docker-compose logs -f
            else
                docker compose logs -f
            fi
        fi
        ;;
    "update")
        log_info "🔄 Updating The Lab Verse Monitoring Stack..."
        git pull origin main
        if command -v docker-compose &> /dev/null; then
            docker-compose build --no-cache
            docker-compose up -d
        else
            docker compose build --no-cache
            docker compose up -d
        fi
        log_success "Stack updated!"
        ;;
    "reset")
        echo -e "${RED}⚠️  This will destroy all data and containers!${NC}"
        read -p "Are you sure? [y/N] " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            if command -v docker-compose &> /dev/null; then
                docker-compose down -v --remove-orphans
            else
                docker compose down -v --remove-orphans
            fi
            docker system prune -af --volumes
            log_success "Stack reset completed"
        fi
        ;;
    "help"|"-h"|"--help")
        echo -e "${BOLD}The Lab Verse Monitoring Stack - Quick Setup${NC}"
        echo
        echo "Usage: $0 [command]"
        echo
        echo "Commands:"
        echo "  install  - Full installation and setup (default)"
        echo "  start    - Start all services"
        echo "  stop     - Stop all services"
        echo "  restart  - Restart all services" 
        echo "  status   - Show service status"
        echo "  logs     - Show service logs (optionally specify service name)"
        echo "  update   - Update stack from git and rebuild"
        echo "  reset    - Reset everything (DESTRUCTIVE)"
        echo "  help     - Show this help"
        echo
        ;;
    *)
        log_error "Unknown command: $1"
        echo "Use '$0 help' for available commands"
        exit 1
        ;;
esac