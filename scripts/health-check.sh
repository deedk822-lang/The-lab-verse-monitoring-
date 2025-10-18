#!/bin/bash
# =============================================================================
# Comprehensive Health Check Script
# =============================================================================
# Purpose: Check health of all services in the stack
# Usage: bash scripts/health-check.sh
# =============================================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║              THE LAB VERSE - HEALTH CHECK                    ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════════╝${NC}\n"

# Service endpoints to check
declare -A SERVICES=(
    ["Kimi AI Manager"]="http://localhost:8084/health"
    ["LapVerse Core"]="http://localhost:3000/health"
    ["Grafana Dashboard"]="http://localhost:3001/api/health"
    ["Prometheus"]="http://localhost:9090/-/healthy"
    ["AlertManager"]="http://localhost:9093/-/healthy"
)

healthy_count=0
unhealthy_count=0
total_count=${#SERVICES[@]}

echo -e "${CYAN}Checking ${total_count} services...${NC}\n"

for service in "${!SERVICES[@]}"; do
    endpoint="${SERVICES[$service]}"
    
    printf "%-25s " "$service:"
    
    if curl -sf --max-time 10 "$endpoint" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ HEALTHY${NC}"
        ((healthy_count++))
    else
        echo -e "${RED}❌ UNHEALTHY${NC}"
        ((unhealthy_count++))
    fi
done

echo -e "\n${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "Total Services: ${total_count}"
echo -e "${GREEN}Healthy: ${healthy_count}${NC}"
echo -e "${RED}Unhealthy: ${unhealthy_count}${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}\n"

# Check Docker containers
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
elif docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
else
    echo -e "${YELLOW}⚠️  Docker Compose not available for container checks${NC}"
    exit 0
fi

echo -e "${CYAN}Docker Container Status:${NC}\n"
$DOCKER_COMPOSE ps

# Overall status
echo
if [ $unhealthy_count -eq 0 ]; then
    echo -e "${GREEN}${BOLD}✅ ALL SERVICES HEALTHY${NC}"
    exit 0
else
    echo -e "${RED}${BOLD}❌ ${unhealthy_count} SERVICE(S) UNHEALTHY${NC}"
    echo -e "${YELLOW}Check logs with: docker-compose logs <service-name>${NC}"
    exit 1
fi