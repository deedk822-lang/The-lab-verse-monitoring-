#!/bin/bash
# ============================================================================
# VAAL AI Empire - Live Monitoring Dashboard
# ============================================================================
# Real-time credit usage monitoring dashboard
#
# Usage:
#   ./scripts/dashboard.sh
# ============================================================================

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'
BOLD='\033[1m'

# Activate venv if exists
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

# Function to get usage data
get_usage_data() {
    python3 <<PYTHON
import json
from vaal_ai_empire.credit_protection.manager import get_manager

manager = get_manager()
usage = manager.get_usage_summary()
print(json.dumps(usage))
PYTHON
}

# Function to draw progress bar
draw_progress_bar() {
    local percent=$1
    local width=50
    local filled=$((percent * width / 100))
    local empty=$((width - filled))
    
    # Color based on percentage
    if [ $percent -ge 90 ]; then
        color=$RED
    elif [ $percent -ge 70 ]; then
        color=$YELLOW
    else
        color=$GREEN
    fi
    
    printf "${color}"
    printf '%*s' $filled | tr ' ' '█'
    printf "${NC}"
    printf '%*s' $empty | tr ' ' '░'
    printf " %3d%%" $percent
}

# Main dashboard loop
while true; do
    clear
    
    # Header
    echo -e "${BOLD}${CYAN}================================================================${NC}"
    echo -e "${BOLD}${CYAN}       VAAL AI EMPIRE - CREDIT PROTECTION DASHBOARD${NC}"
    echo -e "${BOLD}${CYAN}================================================================${NC}"
    echo ""
    
    # Get usage data
    usage_json=$(get_usage_data)
    
    # Parse JSON
    tier=$(echo "$usage_json" | jq -r '.tier')
    
    daily_requests=$(echo "$usage_json" | jq -r '.daily.requests')
    daily_requests_limit=$(echo "$usage_json" | jq -r '.daily.limits.requests')
    daily_requests_percent=$(echo "$usage_json" | jq -r '.daily.usage_percent.requests' | awk '{print int($1)}')
    
    daily_tokens=$(echo "$usage_json" | jq -r '.daily.tokens')
    daily_tokens_limit=$(echo "$usage_json" | jq -r '.daily.limits.tokens')
    daily_tokens_percent=$(echo "$usage_json" | jq -r '.daily.usage_percent.tokens' | awk '{print int($1)}')
    
    daily_cost=$(echo "$usage_json" | jq -r '.daily.cost_usd')
    daily_cost_limit=$(echo "$usage_json" | jq -r '.daily.limits.cost_usd')
    daily_cost_percent=$(echo "$usage_json" | jq -r '.daily.usage_percent.cost' | awk '{print int($1)}')
    
    hourly_requests=$(echo "$usage_json" | jq -r '.hourly.requests')
    hourly_requests_limit=$(echo "$usage_json" | jq -r '.hourly.limits.requests')
    
    circuit_open=$(echo "$usage_json" | jq -r '.circuit_breaker.open')
    circuit_until=$(echo "$usage_json" | jq -r '.circuit_breaker.until')
    
    # Display tier
    echo -e "${BOLD}Tier:${NC} ${MAGENTA}${tier^^}${NC}"
    echo ""
    
    # Daily usage
    echo -e "${BOLD}${BLUE}■ DAILY USAGE${NC}"
    echo -e "${CYAN}├─ Requests:${NC} $daily_requests / $daily_requests_limit"
    echo -n "${CYAN}│  ${NC}"
    draw_progress_bar $daily_requests_percent
    echo ""
    echo ""
    
    echo -e "${CYAN}├─ Tokens:${NC} $(printf "%'d" $daily_tokens) / $(printf "%'d" $daily_tokens_limit)"
    echo -n "${CYAN}│  ${NC}"
    draw_progress_bar $daily_tokens_percent
    echo ""
    echo ""
    
    echo -e "${CYAN}└─ Cost:${NC} \$$daily_cost / \$$daily_cost_limit USD"
    echo -n "   "
    draw_progress_bar $daily_cost_percent
    echo ""
    echo ""
    
    # Hourly usage
    echo -e "${BOLD}${BLUE}■ HOURLY USAGE (Burst Protection)${NC}"
    echo -e "${CYAN}└─ Requests:${NC} $hourly_requests / $hourly_requests_limit"
    echo ""
    
    # Circuit breaker status
    echo -e "${BOLD}${BLUE}■ CIRCUIT BREAKER${NC}"
    if [ "$circuit_open" = "true" ]; then
        echo -e "${CYAN}└─ Status:${NC} ${RED}${BOLD}⚠ OPEN (BLOCKING REQUESTS)${NC}"
        echo -e "${CYAN}   Until:${NC} $circuit_until"
    else
        echo -e "${CYAN}└─ Status:${NC} ${GREEN}✓ CLOSED (OPERATIONAL)${NC}"
    fi
    echo ""
    
    # Resource usage (if psutil available)
    if python3 -c "import psutil" 2>/dev/null; then
        resources=$(python3 <<PYTHON
import psutil
import json

data = {
    'cpu': psutil.cpu_percent(interval=1),
    'memory': psutil.virtual_memory().percent,
    'disk': psutil.disk_usage('/').percent
}
print(json.dumps(data))
PYTHON
)
        
        cpu=$(echo "$resources" | jq -r '.cpu' | awk '{print int($1)}')
        memory=$(echo "$resources" | jq -r '.memory' | awk '{print int($1)}')
        disk=$(echo "$resources" | jq -r '.disk' | awk '{print int($1)}')
        
        echo -e "${BOLD}${BLUE}■ SYSTEM RESOURCES${NC}"
        echo -e "${CYAN}├─ CPU:${NC}"
        echo -n "${CYAN}│  ${NC}"
        draw_progress_bar $cpu
        echo ""
        
        echo -e "${CYAN}├─ Memory:${NC}"
        echo -n "${CYAN}│  ${NC}"
        draw_progress_bar $memory
        echo ""
        
        echo -e "${CYAN}└─ Disk:${NC}"
        echo -n "   "
        draw_progress_bar $disk
        echo ""
    fi
    
    # Footer
    echo ""
    echo -e "${CYAN}================================================================${NC}"
    echo -e "Last updated: $(date '+%Y-%m-%d %H:%M:%S')"
    echo -e "Press ${BOLD}Ctrl+C${NC} to exit | Refreshing every 5 seconds..."
    
    sleep 5
done
