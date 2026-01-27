#!/bin/bash
#
# VAAL AI Empire - Emergency Shutdown Script
# Immediately stops all LLM services and triggers circuit breaker
#

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${RED}"
cat << "EOF"
╔═══════════════════════════════════════════════════╗
║       🚨 EMERGENCY SHUTDOWN INITIATED 🚨         ║
╚═══════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

echo -e "${YELLOW}This will:${NC}"
echo -e "  1. Trigger the circuit breaker"
echo -e "  2. Block all new LLM requests"
echo -e "  3. Stop the credit protection service"
echo -e "  4. Kill any running LLM processes"
echo ""
read -p "Are you sure? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo -e "${GREEN}Shutdown cancelled${NC}"
    exit 0
fi

echo ""
echo -e "${RED}[1/4] Triggering circuit breaker...${NC}"
python3 << 'PYTHON'
from vaal_ai_empire.credit_protection import get_manager
manager = get_manager()
manager.trigger_circuit_breaker(duration_minutes=120)
print("✓ Circuit breaker activated for 2 hours")
PYTHON

echo -e "${RED}[2/4] Stopping credit protection service...${NC}"
if systemctl is-active --quiet credit-protection; then
    sudo systemctl stop credit-protection
    echo -e "${GREEN}✓ Service stopped${NC}"
else
    echo -e "${YELLOW}⚠ Service not running${NC}"
fi

echo -e "${RED}[3/4] Killing LLM processes...${NC}"
# Kill any Python processes related to LLM
pkill -f "huggingface" || true
pkill -f "transformers" || true
pkill -f "llm_provider" || true
echo -e "${GREEN}✓ Processes terminated${NC}"

echo -e "${RED}[4/4] Creating lockfile...${NC}"
touch /var/lib/vaal/EMERGENCY_SHUTDOWN
echo "$(date -Iseconds)" > /var/lib/vaal/EMERGENCY_SHUTDOWN
echo -e "${GREEN}✓ Lockfile created${NC}"

echo ""
echo -e "${RED}"
cat << "EOF"
╔═══════════════════════════════════════════════════╗
║          EMERGENCY SHUTDOWN COMPLETE             ║
╚═══════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

echo -e "${YELLOW}All LLM requests are now blocked.${NC}"
echo ""
echo -e "${BLUE}To resume normal operation:${NC}"
echo -e "  1. Remove lockfile: ${CYAN}rm /var/lib/vaal/EMERGENCY_SHUTDOWN${NC}"
echo -e "  2. Reset circuit breaker: ${CYAN}python3 -c 'from vaal_ai_empire.credit_protection import get_manager; get_manager().circuit_open = False'${NC}"
echo -e "  3. Restart service: ${CYAN}sudo systemctl start credit-protection${NC}"
echo ""
