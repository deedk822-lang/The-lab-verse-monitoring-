#!/bin/bash
#
# VAAL AI Empire - Real-time Credit Usage Dashboard
# Live monitoring of quota usage and system health
#

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'

CREDIT_STORAGE="/var/lib/vaal/credit_protection"

get_usage_summary() {
    python3 << 'PYTHON'
import json
import sys
from pathlib import Path
from datetime import datetime

try:
    from vaal_ai_empire.credit_protection import get_manager
    manager = get_manager()
    summary = manager.get_usage_summary()
    print(json.dumps(summary, indent=2))
except Exception as e:
    print(json.dumps({"error": str(e)}), file=sys.stderr)
    sys.exit(1)
PYTHON
}

draw_progress_bar() {
    local percent=$1
    local width=40
    local filled=$(printf "%.0f" $(echo "$width * $percent / 100" | bc -l))
    local empty=$((width - filled))
    
    # Color based on percentage
    local color=$GREEN
    if (( $(echo "$percent >= 90" | bc -l) )); then
        color=$RED
    elif (( $(echo "$percent >= 70" | bc -l) )); then
        color=$YELLOW
    fi
    
    printf "${color}["
    printf '█%.0s' $(seq 1 $filled)
    printf '░%.0s' $(seq 1 $empty)
    printf "]${NC} %5.1f%%" "$percent"
}

while true; do
    clear
    
    echo -e "${BLUE}"
    cat << "EOF"
╔═════════════════════════════════════════════════════════════════════╗
║         VAAL AI EMPIRE - CREDIT PROTECTION DASHBOARD              ║
╚═════════════════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"
    
    # Get usage data
    SUMMARY=$(get_usage_summary 2>/dev/null)
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}Error: Could not load credit usage data${NC}"
        echo -e "${YELLOW}Is the credit protection system initialized?${NC}"
        exit 1
    fi
    
    # Parse JSON
    TIER=$(echo "$SUMMARY" | jq -r '.tier')
    
    # Daily usage
    DAILY_REQUESTS=$(echo "$SUMMARY" | jq -r '.daily.requests')
    DAILY_TOKENS=$(echo "$SUMMARY" | jq -r '.daily.tokens')
    DAILY_COST=$(echo "$SUMMARY" | jq -r '.daily.cost_usd')
    
    DAILY_REQUESTS_LIMIT=$(echo "$SUMMARY" | jq -r '.daily.limits.requests')
    DAILY_TOKENS_LIMIT=$(echo "$SUMMARY" | jq -r '.daily.limits.tokens')
    DAILY_COST_LIMIT=$(echo "$SUMMARY" | jq -r '.daily.limits.cost_usd')
    
    DAILY_REQUESTS_PCT=$(echo "$SUMMARY" | jq -r '.daily.usage_percent.requests')
    DAILY_TOKENS_PCT=$(echo "$SUMMARY" | jq -r '.daily.usage_percent.tokens')
    DAILY_COST_PCT=$(echo "$SUMMARY" | jq -r '.daily.usage_percent.cost')
    
    # Hourly usage
    HOURLY_REQUESTS=$(echo "$SUMMARY" | jq -r '.hourly.requests')
    HOURLY_TOKENS=$(echo "$SUMMARY" | jq -r '.hourly.tokens')
    HOURLY_COST=$(echo "$SUMMARY" | jq -r '.hourly.cost_usd')
    
    HOURLY_REQUESTS_LIMIT=$(echo "$SUMMARY" | jq -r '.hourly.limits.requests')
    HOURLY_TOKENS_LIMIT=$(echo "$SUMMARY" | jq -r '.hourly.limits.tokens')
    HOURLY_COST_LIMIT=$(echo "$SUMMARY" | jq -r '.hourly.limits.cost_usd')
    
    # Circuit breaker
    CIRCUIT_OPEN=$(echo "$SUMMARY" | jq -r '.circuit_breaker.open')
    CIRCUIT_UNTIL=$(echo "$SUMMARY" | jq -r '.circuit_breaker.until')
    
    # Header info
    echo -e "${CYAN}Tier:${NC} ${MAGENTA}$(echo $TIER | tr '[:lower:]' '[:upper:]')${NC}"
    echo -e "${CYAN}Time:${NC} $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""
    
    # Circuit breaker status
    if [ "$CIRCUIT_OPEN" = "true" ]; then
        echo -e "${RED}╔═══════════════════════════════════════════════════════════════════╗${NC}"
        echo -e "${RED}║  🚨 CIRCUIT BREAKER ACTIVE - All requests blocked until:        ║${NC}"
        echo -e "${RED}║     $CIRCUIT_UNTIL                                ║${NC}"
        echo -e "${RED}╚═══════════════════════════════════════════════════════════════════╝${NC}"
        echo ""
    fi
    
    # Daily usage
    echo -e "${BLUE}═══ DAILY USAGE ═══${NC}"
    echo ""
    echo -e "${CYAN}Requests:${NC} $DAILY_REQUESTS / $DAILY_REQUESTS_LIMIT"
    draw_progress_bar "$DAILY_REQUESTS_PCT"
    echo ""
    echo ""
    
    echo -e "${CYAN}Tokens:${NC} $(printf "%'d" $DAILY_TOKENS) / $(printf "%'d" $DAILY_TOKENS_LIMIT)"
    draw_progress_bar "$DAILY_TOKENS_PCT"
    echo ""
    echo ""
    
    echo -e "${CYAN}Cost:${NC} \$$DAILY_COST / \$$DAILY_COST_LIMIT"
    draw_progress_bar "$DAILY_COST_PCT"
    echo ""
    echo ""
    
    # Hourly usage
    echo -e "${BLUE}═══ CURRENT HOUR USAGE ═══${NC}"
    echo ""
    echo -e "${CYAN}Requests:${NC} $HOURLY_REQUESTS / $HOURLY_REQUESTS_LIMIT"
    HOURLY_REQUESTS_PCT=$(echo "scale=2; ($HOURLY_REQUESTS / $HOURLY_REQUESTS_LIMIT) * 100" | bc)
    draw_progress_bar "$HOURLY_REQUESTS_PCT"
    echo ""
    echo ""
    
    echo -e "${CYAN}Tokens:${NC} $(printf "%'d" $HOURLY_TOKENS) / $(printf "%'d" $HOURLY_TOKENS_LIMIT)"
    HOURLY_TOKENS_PCT=$(echo "scale=2; ($HOURLY_TOKENS / $HOURLY_TOKENS_LIMIT) * 100" | bc)
    draw_progress_bar "$HOURLY_TOKENS_PCT"
    echo ""
    echo ""
    
    # System info
    echo -e "${BLUE}═══ SYSTEM RESOURCES ═══${NC}"
    CPU=$(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - $1}')
    MEM=$(free | grep Mem | awk '{printf "%.1f", $3/$2 * 100.0}')
    DISK=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
    
    echo -e "${CYAN}CPU:${NC}"
    draw_progress_bar "$CPU"
    echo ""
    echo ""
    
    echo -e "${CYAN}Memory:${NC}"
    draw_progress_bar "$MEM"
    echo ""
    echo ""
    
    echo -e "${CYAN}Disk:${NC}"
    draw_progress_bar "$DISK"
    echo ""
    echo ""
    
    echo -e "${YELLOW}Press Ctrl+C to exit | Updates every 5 seconds${NC}"
    
    sleep 5
done
