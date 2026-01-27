#!/bin/bash
# ============================================================================
# VAAL AI Empire - Alibaba Cloud Credit Protection Setup
# ============================================================================
# This script sets up the credit protection system on Alibaba Cloud ECS
# with automated monitoring, alerts, and circuit breakers.
#
# Usage:
#   chmod +x scripts/setup-alibaba-cloud-protection.sh
#   sudo ./scripts/setup-alibaba-cloud-protection.sh
# ============================================================================

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[✓]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[!]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   log_error "This script must be run as root (use sudo)"
   exit 1
fi

log_info "Starting VAAL AI Empire Credit Protection Setup..."

# ============================================================================
# 1. System Preparation
# ============================================================================
log_info "Step 1: Preparing system..."

# Update system
apt-get update -qq
apt-get upgrade -y -qq

# Install system dependencies
apt-get install -y -qq \
    python3.10 \
    python3.10-venv \
    python3-pip \
    git \
    curl \
    wget \
    htop \
    postgresql-client \
    redis-tools

log_success "System prepared"

# ============================================================================
# 2. Create directories
# ============================================================================
log_info "Step 2: Creating directories..."

mkdir -p /var/lib/vaal/credit_protection
mkdir -p /var/log/vaal
mkdir -p /etc/vaal
mkdir -p /opt/vaal-ai-empire

chown -R $SUDO_USER:$SUDO_USER /var/lib/vaal
chown -R $SUDO_USER:$SUDO_USER /var/log/vaal
chown -R $SUDO_USER:$SUDO_USER /etc/vaal
chown -R $SUDO_USER:$SUDO_USER /opt/vaal-ai-empire

log_success "Directories created"

# ============================================================================
# 3. Clone repository (if not already)
# ============================================================================
log_info "Step 3: Setting up application..."

if [ ! -d "/opt/vaal-ai-empire/.git" ]; then
    log_info "Cloning repository..."
    git clone https://github.com/deedk822-lang/The-lab-verse-monitoring-.git /opt/vaal-ai-empire
    cd /opt/vaal-ai-empire
else
    log_info "Repository already exists, pulling latest..."
    cd /opt/vaal-ai-empire
    git pull
fi

log_success "Application ready"

# ============================================================================
# 4. Python environment
# ============================================================================
log_info "Step 4: Setting up Python environment..."

python3.10 -m venv /opt/vaal-ai-empire/venv
source /opt/vaal-ai-empire/venv/bin/activate

pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

log_success "Python environment configured"

# ============================================================================
# 5. Environment configuration
# ============================================================================
log_info "Step 5: Configuring environment..."

if [ ! -f "/etc/vaal/.env" ]; then
    log_info "Creating .env file..."
    cp .env.example /etc/vaal/.env
    
    # Generate secrets
    SECRET_KEY=$(openssl rand -hex 32)
    JWT_SECRET=$(openssl rand -hex 32)
    HEALING_KEY=$(openssl rand -hex 32)
    
    # Update .env with generated secrets
    sed -i "s/your_secret_key_here_generate_with_openssl/$SECRET_KEY/" /etc/vaal/.env
    sed -i "s/your_jwt_secret_key_here/$JWT_SECRET/" /etc/vaal/.env
    sed -i "s/your_self_healing_key_here/$HEALING_KEY/" /etc/vaal/.env
    
    log_warning "Please edit /etc/vaal/.env and add your API keys:"
    log_warning "  - HF_TOKEN (HuggingFace)"
    log_warning "  - OPENAI_API_KEY (if using OpenAI)"
    log_warning "  - Email/webhook settings for alerts"
else
    log_info ".env already exists, skipping..."
fi

# Create symlink
ln -sf /etc/vaal/.env /opt/vaal-ai-empire/.env

log_success "Environment configured"

# ============================================================================
# 6. Systemd service
# ============================================================================
log_info "Step 6: Installing systemd service..."

cat > /etc/systemd/system/vaal-credit-protection.service <<'EOF'
[Unit]
Description=VAAL AI Empire Credit Protection Monitor
After=network.target postgresql.service redis.service
Wants=postgresql.service redis.service

[Service]
Type=simple
User=vaal
Group=vaal
WorkingDirectory=/opt/vaal-ai-empire
EnvironmentFile=/etc/vaal/.env
ExecStart=/opt/vaal-ai-empire/venv/bin/python -m vaal_ai_empire.credit_protection.monitor_service
Restart=always
RestartSec=10

# Logging
StandardOutput=append:/var/log/vaal/credit-protection.log
StandardError=append:/var/log/vaal/credit-protection-error.log

# Security
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/var/lib/vaal /var/log/vaal

[Install]
WantedBy=multi-user.target
EOF

# Create vaal user if not exists
if ! id "vaal" &>/dev/null; then
    useradd -r -s /bin/false vaal
    usermod -aG $SUDO_USER vaal
fi

chown -R vaal:vaal /var/lib/vaal /var/log/vaal /opt/vaal-ai-empire

systemctl daemon-reload
systemctl enable vaal-credit-protection.service

log_success "Systemd service installed"

# ============================================================================
# 7. Log rotation
# ============================================================================
log_info "Step 7: Setting up log rotation..."

cat > /etc/logrotate.d/vaal <<'EOF'
/var/log/vaal/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 vaal vaal
    sharedscripts
    postrotate
        systemctl reload vaal-credit-protection.service > /dev/null 2>&1 || true
    endscript
}
EOF

log_success "Log rotation configured"

# ============================================================================
# 8. Firewall (optional)
# ============================================================================
log_info "Step 8: Configuring firewall..."

if command -v ufw &> /dev/null; then
    ufw allow 8000/tcp comment 'VAAL API'
    ufw allow 9090/tcp comment 'Prometheus'
    log_success "Firewall configured"
else
    log_warning "UFW not installed, skipping firewall configuration"
fi

# ============================================================================
# 9. Health check script
# ============================================================================
log_info "Step 9: Creating health check script..."

cat > /usr/local/bin/vaal-health-check <<'EOF'
#!/bin/bash
set -e

source /etc/vaal/.env
source /opt/vaal-ai-empire/venv/bin/activate

python3 <<PYTHON
import sys
from vaal_ai_empire.credit_protection.manager import get_manager

try:
    manager = get_manager()
    usage = manager.get_usage_summary()
    
    print(f"Tier: {usage['tier']}")
    print(f"Daily Usage: {usage['daily']['requests']}/{usage['daily']['limits']['requests']} requests")
    print(f"Daily Cost: \${usage['daily']['cost_usd']:.4f}/\${usage['daily']['limits']['cost_usd']:.2f}")
    print(f"Circuit Breaker: {'OPEN' if usage['circuit_breaker']['open'] else 'CLOSED'}")
    
    # Exit with error if circuit breaker is open
    sys.exit(1 if usage['circuit_breaker']['open'] else 0)
except Exception as e:
    print(f"Health check failed: {e}")
    sys.exit(1)
PYTHON
EOF

chmod +x /usr/local/bin/vaal-health-check

log_success "Health check script created"

# ============================================================================
# 10. Cron jobs
# ============================================================================
log_info "Step 10: Setting up cron jobs..."

# Add health check to crontab
(crontab -u vaal -l 2>/dev/null || true; echo "*/5 * * * * /usr/local/bin/vaal-health-check >> /var/log/vaal/health-check.log 2>&1") | crontab -u vaal -

log_success "Cron jobs configured"

# ============================================================================
# Summary
# ============================================================================
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✓ Credit Protection Setup Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
log_info "Next steps:"
echo "  1. Edit /etc/vaal/.env with your API keys"
echo "  2. Configure email/webhook alerts (optional)"
echo "  3. Start the service: systemctl start vaal-credit-protection"
echo "  4. Check status: systemctl status vaal-credit-protection"
echo "  5. View logs: journalctl -u vaal-credit-protection -f"
echo "  6. Run health check: /usr/local/bin/vaal-health-check"
echo ""
log_info "Monitoring dashboard: ./scripts/dashboard.sh"
log_info "Emergency shutdown: ./scripts/emergency-shutdown.sh"
echo ""
