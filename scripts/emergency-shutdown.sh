#!/bin/bash
# ============================================================================
# VAAL AI Empire - Emergency Shutdown
# ============================================================================
# Emergency shutdown script to immediately stop all LLM requests
# and prevent cost overruns
#
# Usage:
#   sudo ./scripts/emergency-shutdown.sh
# ============================================================================

set -euo pipefail

# Colors
RED='\033[0;31m'
YELLOW='\033[1;33m'
BOLD='\033[1m'
NC='\033[0m'

echo -e "${RED}${BOLD}"
echo "========================================"
echo "   ⚠  EMERGENCY SHUTDOWN INITIATED"
echo "========================================"
echo -e "${NC}"

echo -e "${YELLOW}This will:${NC}"
echo "  1. Trigger circuit breaker (block all requests)"
echo "  2. Stop credit protection service"
echo "  3. Stop API server"
echo ""
read -p "Are you sure? (type 'yes' to confirm): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Aborted."
    exit 1
fi

echo ""
echo "[1/3] Triggering circuit breaker..."
python3 <<PYTHON
from vaal_ai_empire.credit_protection.manager import get_manager

manager = get_manager()
manager.trigger_circuit_breaker(duration_minutes=1440)  # 24 hours
print("✓ Circuit breaker activated for 24 hours")
PYTHON

echo ""
echo "[2/3] Stopping credit protection service..."
if systemctl is-active --quiet vaal-credit-protection; then
    systemctl stop vaal-credit-protection
    echo "✓ Service stopped"
else
    echo "ℹ Service not running"
fi

echo ""
echo "[3/3] Stopping API server..."
if pgrep -f "uvicorn.*vaal" > /dev/null; then
    pkill -f "uvicorn.*vaal"
    echo "✓ API server stopped"
else
    echo "ℹ API server not running"
fi

echo ""
echo -e "${RED}${BOLD}"
echo "========================================"
echo "   ✓ EMERGENCY SHUTDOWN COMPLETE"
echo "========================================"
echo -e "${NC}"
echo ""
echo "All LLM requests are now BLOCKED."
echo "Circuit breaker will remain active for 24 hours."
echo ""
echo "To resume operations:"
echo "  1. Investigate the issue"
echo "  2. Review usage logs: /var/log/vaal/"
echo "  3. Reset circuit breaker manually if needed"
echo "  4. Restart services: systemctl start vaal-credit-protection"
echo ""
