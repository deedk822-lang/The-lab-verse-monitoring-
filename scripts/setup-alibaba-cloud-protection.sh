#!/bin/bash
#
# VAAL AI Empire - Credit Protection Setup Script
# Automated installation for Alibaba Cloud instances
#

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}"
cat << "EOF"
╦  ╦╔═╗╔═╗╦    ╔═╗╦  ╔═╗╔╦╗╔═╗╦╦═╗╔═╗
╚╗╔╝╠═╣╠═╣║    ║╣ ║║║╠═╝║║║╠╦╝║╣ 
 ╚╝ ╩ ╩╩ ╩╩═╝  ╚═╝╩ ╩╩  ╩╩ ╩╩╚═╚═╝
Credit Protection Setup
EOF
echo -e "${NC}"

echo -e "${GREEN}[1/10] Checking system requirements...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 not found${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
if (( $(echo "$PYTHON_VERSION < 3.8" | bc -l) )); then
    echo -e "${RED}Error: Python 3.8+ required (found $PYTHON_VERSION)${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Python $PYTHON_VERSION detected${NC}"

echo -e "${GREEN}[2/10] Installing system dependencies...${NC}"
sudo apt-get update -qq
sudo apt-get install -y -qq \
    python3-pip \
    python3-venv \
    git \
    curl \
    jq \
    bc \
    psmisc 

echo -e "${GREEN}[3/10] Creating directories...${NC}"
sudo mkdir -p /var/lib/vaal/credit_protection
sudo mkdir -p /var/log/vaal
sudo mkdir -p /etc/vaal
sudo chown -R $USER:$USER /var/lib/vaal /var/log/vaal /etc/vaal

echo -e "${GREEN}[4/10] Setting up Python virtual environment...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate

echo -e "${GREEN}[5/10] Installing Python dependencies...${NC}"
pip install --upgrade pip -q
pip install -r requirements.txt -q

echo -e "${GREEN}[6/10] Configuring environment...${NC}"
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo -e "${YELLOW}⚠ Please edit .env file with your API keys${NC}"
    echo -e "${YELLOW}  Required: HF_TOKEN, CREDIT_TIER${NC}"
    read -p "Press Enter to open .env in nano..."
    nano .env
else
    echo -e "${YELLOW}⚠ .env file already exists, skipping${NC}"
fi

echo -e "${GREEN}[7/10] Verifying configuration...${NC}"
source .env

if [ -z "$HF_TOKEN" ] || [ "$HF_TOKEN" = "your_huggingface_token_here" ]; then
    echo -e "${RED}Error: HF_TOKEN not configured in .env${NC}"
    exit 1
fi

if [ -z "$CREDIT_TIER" ]; then
    echo -e "${YELLOW}Warning: CREDIT_TIER not set, defaulting to 'free'${NC}"
    export CREDIT_TIER=free
fi

echo -e "${GREEN}✓ Tier: $CREDIT_TIER${NC}"

echo -e "${GREEN}[8/10] Installing systemd service...${NC}"
sudo cp scripts/systemd/credit-protection.service /etc/systemd/system/
sudo sed -i "s|/path/to/vaal|$(pwd)|g" /etc/systemd/system/credit-protection.service
sudo sed -i "s|User=vaal|User=$USER|g" /etc/systemd/system/credit-protection.service
sudo systemctl daemon-reload

echo -e "${GREEN}[9/10] Testing credit protection...${NC}"
python3 -c "
from vaal_ai_empire.credit_protection import get_manager
manager = get_manager()
print(f'✓ Credit manager initialized: {manager.tier.value} tier')
print(f'✓ Daily limit: {manager.quota.daily_requests} requests')
print(f'✓ Storage: {manager.storage_path}')
"

echo -e "${GREEN}[10/10] Setting up monitoring scripts...${NC}"
chmod +x scripts/dashboard.sh
chmod +x scripts/emergency-shutdown.sh

echo -e "${GREEN}"
cat << "EOF"
╔═══════════════════════════════════════════════════════╗
║  ✓ Credit Protection System Installed Successfully   ║
╚═══════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

echo -e "${BLUE}Next Steps:${NC}"
echo -e "${YELLOW}1. Start the service:${NC}"
echo -e "   sudo systemctl start credit-protection"
echo -e "   sudo systemctl enable credit-protection  # Auto-start on boot"
echo ""
echo -e "${YELLOW}2. Check service status:${NC}"
echo -e "   sudo systemctl status credit-protection"
echo ""
echo -e "${YELLOW}3. View live dashboard:${NC}"
echo -e "   ./scripts/dashboard.sh"
echo ""
echo -e "${YELLOW}4. Emergency shutdown:${NC}"
echo -e "   ./scripts/emergency-shutdown.sh"
echo ""
echo -e "${YELLOW}5. View logs:${NC}"
echo -e "   tail -f /var/log/vaal/credit-protection.log"
echo ""
echo -e "${GREEN}Configuration:${NC}"
echo -e "  Tier: ${BLUE}$CREDIT_TIER${NC}"
echo -e "  Storage: ${BLUE}/var/lib/vaal/credit_protection${NC}"
echo -e "  Logs: ${BLUE}/var/log/vaal${NC}"
echo ""
echo -e "${RED}IMPORTANT: Keep your .env file secure and never commit it to git!${NC}"
