#!/bin/bash
# =============================================================================
# VAAL AI Empire - Production Installation Script for Alibaba Cloud Singapore
# =============================================================================
# Region: ap-southeast-1 (Singapore)
#
# Usage:
#   sudo bash install.sh
#
# Prerequisites:
#   - Alibaba Cloud ECS instance (Ubuntu 22.04 LTS)
#   - Root or sudo access
#   - Internet connectivity
# =============================================================================

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
INSTALL_DIR="/opt/vaal-ai-empire"
CONFIG_DIR="/etc/vaal"
DATA_DIR="/var/lib/vaal"
LOG_DIR="/var/log/vaal"
SERVICE_NAME="vaal-ai-empire"

# Logging
LOG_FILE="/var/log/vaal-install.log"

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] ✓${NC} $1" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] ⚠${NC} $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ✗${NC} $1" | tee -a "$LOG_FILE"
}

# =============================================================================
# Pre-flight Checks
# =============================================================================

check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root or with sudo"
        exit 1
    fi
}

check_os() {
    if [[ ! -f /etc/os-release ]]; then
        log_error "Cannot detect OS version"
        exit 1
    fi
    
    source /etc/os-release
    log "Detected OS: $NAME $VERSION_ID"
    
    if [[ "$ID" != "ubuntu" && "$ID" != "debian" ]]; then
        log_warning "This script is tested on Ubuntu/Debian"
        log_warning "Your OS ($ID) may not be fully supported"
        read -p "Continue anyway? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

check_internet() {
    log "Checking internet connectivity..."
    if ! ping -c 1 8.8.8.8 &> /dev/null; then
        log_error "No internet connectivity detected"
        exit 1
    fi
    log_success "Internet connectivity confirmed"
}

# =============================================================================
# System Dependencies
# =============================================================================

install_docker() {
    log "Installing Docker..."
    
    if command -v docker &> /dev/null; then
        log_success "Docker already installed: $(docker --version)"
        return
    fi
    
    apt-get update
    apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release
    
    curl -fsSL https://download.docker.com/linux/$ID/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/$ID $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    apt-get update
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    
    usermod -aG docker $SUDO_USER 2>/dev/null || true
    
    log_success "Docker installed: $(docker --version)"
}

install_docker_compose() {
    log "Installing Docker Compose..."
    
    if docker compose version &> /dev/null; then
        log_success "Docker Compose already installed"
        return
    fi
    
    COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep 'tag_name' | cut -d\" -f4)
    mkdir -p /usr/local/lib/docker/cli-plugins
    curl -SL "https://github.com/docker/compose/releases/download/${COMPOSE_VERSION}/docker-compose-linux-$(uname -m)" -o /usr/local/lib/docker/cli-plugins/docker-compose
    chmod +x /usr/local/lib/docker/cli-plugins/docker-compose
    ln -sf /usr/local/lib/docker/cli-plugins/docker-compose /usr/local/bin/docker-compose
    
    log_success "Docker Compose installed: $(docker compose version)"
}

install_utils() {
    log "Installing utility packages..."
    apt-get install -y curl wget jq net-tools htop vim
    log_success "Utilities installed"
}

# =============================================================================
# Directory Setup
# =============================================================================

setup_directories() {
    log "Setting up directories..."
    
    mkdir -p "$INSTALL_DIR"
    mkdir -p "$CONFIG_DIR"
    mkdir -p "$DATA_DIR"/{logs,cache,backups}
    mkdir -p "$LOG_DIR"
    mkdir -p /etc/systemd/system
    
    if [[ -n "$SUDO_USER" ]]; then
        chown -R "$SUDO_USER:$SUDO_USER" "$DATA_DIR" 2>/dev/null || true
    fi
    
    log_success "Directories created"
}

# =============================================================================
# Application Setup
# =============================================================================

copy_application() {
    log "Copying application files..."
    
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    
    # Copy all files except .git
    rsync -av --exclude='.git' --exclude='*.pyc' --exclude='__pycache__' "$SCRIPT_DIR/" "$INSTALL_DIR/" 2>/dev/null || \
        cp -r "$SCRIPT_DIR"/* "$INSTALL_DIR/" 2>/dev/null
    
    chmod +x "$INSTALL_DIR/install.sh" 2>/dev/null || true
    
    log_success "Application files copied to $INSTALL_DIR"
}

setup_environment() {
    log "Setting up environment configuration..."
    
    ENV_FILE="$INSTALL_DIR/.env"
    
    if [[ -f "$ENV_FILE" ]] && [[ -s "$ENV_FILE" ]]; then
        log_warning ".env file already exists with content"
        read -p "Overwrite with new configuration? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log "Keeping existing .env file"
            return
        fi
    fi
    
    # Copy example env
    cp "$INSTALL_DIR/.env.example" "$ENV_FILE"
    
    # Generate secure passwords
    POSTGRES_PASS=$(openssl rand -base64 32 | tr -dc 'a-zA-Z0-9' | head -c 24)
    REDIS_PASS=$(openssl rand -base64 32 | tr -dc 'a-zA-Z0-9' | head -c 24)
    ADMIN_SECRET=$(openssl rand -base64 32 | tr -dc 'a-zA-Z0-9' | head -c 32)
    SELF_HEALING_KEY=$(openssl rand -hex 32)
    
    # Update .env file
    sed -i "s/change_this_secure_password/$POSTGRES_PASS/g" "$ENV_FILE"
    sed -i "s/change_this_redis_password/$REDIS_PASS/g" "$ENV_FILE"
    sed -i "s/your_secure_admin_secret_here/$ADMIN_SECRET/g" "$ENV_FILE"
    sed -i "s/your-secure-random-key-here/$SELF_HEALING_KEY/g" "$ENV_FILE"
    
    log_success "Environment file created at $ENV_FILE"
    log_warning "IMPORTANT: Edit $ENV_FILE to add your KIMIAPIKEY"
}

# =============================================================================
# Systemd Service
# =============================================================================

setup_systemd() {
    log "Setting up systemd service..."
    
    cat > /etc/systemd/system/${SERVICE_NAME}.service << 'EOF'
[Unit]
Description=VAAL AI Empire - Production API
Documentation=https://github.com/deedk822-lang/The-lab-verse-monitoring-
Requires=docker.service
After=docker.service network.target

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/vaal-ai-empire
Environment=COMPOSE_PROJECT_NAME=vaal
Environment=DOCKER_CLIENT_TIMEOUT=120
Environment=COMPOSE_HTTP_TIMEOUT=120

# Start
ExecStart=/usr/local/bin/docker-compose up -d

# Stop
ExecStop=/usr/local/bin/docker-compose down

# Reload
ExecReload=/usr/local/bin/docker-compose up -d

[Install]
WantedBy=multi-user.target
EOF
    
    systemctl daemon-reload
    systemctl enable ${SERVICE_NAME}.service
    
    log_success "Systemd service created and enabled"
}

# =============================================================================
# Firewall Configuration
# =============================================================================

configure_firewall() {
    log "Configuring firewall..."
    
    if command -v ufw &> /dev/null; then
        ufw allow 22/tcp
        ufw allow 80/tcp
        ufw allow 443/tcp
        ufw allow 8000/tcp
        ufw allow 9090/tcp
        ufw --force enable
        log_success "UFW firewall configured"
    elif command -v iptables &> /dev/null; then
        iptables -A INPUT -p tcp --dport 22 -j ACCEPT
        iptables -A INPUT -p tcp --dport 80 -j ACCEPT
        iptables -A INPUT -p tcp --dport 443 -j ACCEPT
        iptables -A INPUT -p tcp --dport 8000 -j ACCEPT
        iptables -A INPUT -p tcp --dport 9090 -j ACCEPT
        iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
        log_success "iptables configured"
    fi
}

# =============================================================================
# Build and Start
# =============================================================================

build_application() {
    log "Building Docker images..."
    
    cd "$INSTALL_DIR"
    docker compose build --no-cache
    
    log_success "Docker images built"
}

start_application() {
    log "Starting application..."
    
    cd "$INSTALL_DIR"
    docker compose up -d
    
    log "Waiting for services to start..."
    sleep 15
    
    # Check health
    for i in {1..30}; do
        if curl -sf http://localhost:8000/health &> /dev/null; then
            log_success "Application is healthy!"
            return
        fi
        log "Waiting for application to be ready... ($i/30)"
        sleep 2
    done
    
    log_error "Application failed to start within 60 seconds"
    log "Check logs with: docker compose logs"
    exit 1
}

# =============================================================================
# CLI Tools
# =============================================================================

setup_cli_tools() {
    log "Setting up CLI tools..."
    
    # Dashboard script
    cat > /usr/local/bin/vaal-dashboard << 'EOF'
#!/bin/bash
echo "==================================="
echo "   VAAL AI Empire - Dashboard"
echo "==================================="
echo ""

if ! docker ps | grep -q vaal-app; then
    echo "⚠️  Application is not running!"
    echo "Start with: sudo systemctl start vaal-ai-empire"
    exit 1
fi

echo "📊 Current Usage:"
curl -s http://localhost:8000/api/usage/stats | jq -r '
  "  Tier: \(.tier)",
  "  Tokens: \(.tokens_used) / \(.tokens_limit) (\(.usage_percentage | floor)%)",
  "  Cost: $\(.cost_used) / $\(.cost_limit) (Remaining: $\(.cost_remaining))",
  "  Reset in: \(.reset_in_hours | floor) hours"
' 2>/dev/null || echo "  Unable to fetch stats"

echo ""
echo "🐳 Container Status:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep vaal

echo ""
echo "💾 Resource Usage:"
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" | grep vaal

echo ""
echo "🌐 API Endpoint: http://$(curl -s icanhazip.com 2>/dev/null || echo 'localhost'):8000"
echo "📖 Documentation: http://$(curl -s icanhazip.com 2>/dev/null || echo 'localhost'):8000/docs"
echo ""
echo "Commands: vaal-logs, vaal-stop, vaal-restart, vaal-status"
EOF
    chmod +x /usr/local/bin/vaal-dashboard
    
    # Other CLI tools
    cat > /usr/local/bin/vaal-logs << 'EOF'
#!/bin/bash
cd /opt/vaal-ai-empire && docker compose logs -f "$@"
EOF
    chmod +x /usr/local/bin/vaal-logs
    
    cat > /usr/local/bin/vaal-stop << 'EOF'
#!/bin/bash
cd /opt/vaal-ai-empire && docker compose down
EOF
    chmod +x /usr/local/bin/vaal-stop
    
    cat > /usr/local/bin/vaal-restart << 'EOF'
#!/bin/bash
cd /opt/vaal-ai-empire && docker compose restart
EOF
    chmod +x /usr/local/bin/vaal-restart
    
    cat > /usr/local/bin/vaal-status << 'EOF'
#!/bin/bash
cd /opt/vaal-ai-empire && docker compose ps
EOF
    chmod +x /usr/local/bin/vaal-status
    
    cat > /usr/local/bin/vaal-emergency-stop << 'EOF'
#!/bin/bash
echo "🚨 EMERGENCY STOP INITIATED"
cd /opt/vaal-ai-empire
docker compose down
docker compose exec -T redis redis-cli FLUSHALL 2>/dev/null || true
echo "✅ Application stopped and quota cache cleared"
echo "To restart: sudo systemctl start vaal-ai-empire"
EOF
    chmod +x /usr/local/bin/vaal-emergency-stop
    
    log_success "CLI tools installed"
}

# =============================================================================
# Main Installation
# =============================================================================

main() {
    echo ""
    echo "==================================="
    echo "   VAAL AI Empire - Installer"
    echo "   Region: Singapore (ap-southeast-1)"
    echo "==================================="
    echo ""
    
    mkdir -p /var/log
    touch "$LOG_FILE"
    chmod 644 "$LOG_FILE"
    
    check_root
    check_os
    check_internet
    
    log "Starting installation..."
    
    install_docker
    install_docker_compose
    install_utils
    setup_directories
    copy_application
    setup_environment
    setup_systemd
    configure_firewall
    build_application
    setup_cli_tools
    start_application
    
    echo ""
    echo "==================================="
    echo "   Installation Complete!"
    echo "==================================="
    echo ""
    echo "📍 Installation Directory: $INSTALL_DIR"
    echo "📍 Config: $INSTALL_DIR/.env"
    echo ""
    IP=$(curl -s icanhazip.com 2>/dev/null || echo 'localhost')
    echo "🌐 API Endpoint: http://$IP:8000"
    echo "📖 API Docs: http://$IP:8000/docs"
    echo "❤️  Health: http://$IP:8000/health"
    echo ""
    echo "⚙️  Next Steps:"
    echo "   1. Edit $INSTALL_DIR/.env to add your KIMIAPIKEY"
    echo "   2. Run: sudo systemctl restart vaal-ai-empire"
    echo "   3. Run: vaal-dashboard to monitor"
    echo ""
    echo "📚 Commands:"
    echo "   vaal-dashboard       - Real-time dashboard"
    echo "   vaal-logs            - View logs"
    echo "   vaal-stop            - Stop application"
    echo "   vaal-restart         - Restart application"
    echo "   vaal-emergency-stop  - Emergency stop"
    echo ""
    log_success "Installation completed successfully!"
}

main "$@"
