#!/bin/bash
# =============================================================================
# Docker Compose Configuration Validation Script
# =============================================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🐳 Validating Docker Compose configuration...${NC}\n"

# Check if docker-compose or docker compose is available
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
elif docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
else
    echo -e "${RED}❌ Neither 'docker-compose' nor 'docker compose' found${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker Compose command: $DOCKER_COMPOSE${NC}"

# List of compose files to validate
compose_files=(
    "docker-compose.yml"
    "docker-compose.kimi.yml"
    "docker-compose.security.yml"
)

# Check which files exist
existing_files=()
for file in "${compose_files[@]}"; do
    if [ -f "$file" ]; then
        existing_files+=("-f" "$file")
        echo -e "${GREEN}✅ Found: $file${NC}"
    else
        echo -e "${YELLOW}⚠️  Not found: $file (skipping)${NC}"
    fi
done

if [ ${#existing_files[@]} -eq 0 ]; then
    echo -e "${RED}❌ No Docker Compose files found!${NC}"
    exit 1
fi

# Validate combined configuration
echo -e "\n${BLUE}Validating combined configuration...${NC}"

if $DOCKER_COMPOSE "${existing_files[@]}" config > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Docker Compose configuration is valid${NC}"
    
    # Show merged configuration summary
    echo -e "\n${BLUE}Configuration summary:${NC}"
    $DOCKER_COMPOSE "${existing_files[@]}" config --services | while read service; do
        echo -e "  ${GREEN}✓${NC} $service"
    done
    
    exit 0
else
    echo -e "${RED}❌ Docker Compose configuration is INVALID${NC}"
    echo -e "\nError details:"
    $DOCKER_COMPOSE "${existing_files[@]}" config 2>&1 | head -20
    exit 1
fi