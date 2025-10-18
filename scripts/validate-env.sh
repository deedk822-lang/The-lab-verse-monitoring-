#!/bin/bash
# =============================================================================
# Environment Variables Validation Script
# =============================================================================
# Purpose: Validate .env.local before deployment
# Usage: bash scripts/validate-env.sh
# =============================================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "🔍 Validating environment configuration..."

# Check if .env.local exists
if [ ! -f ".env.local" ]; then
    echo -e "${RED}❌ ERROR: .env.local not found!${NC}"
    echo "Create it from .env.example:"
    echo "  cp .env.example .env.local"
    exit 1
fi

# Check for placeholder values
placeholders_found=false

if grep -q "replace-with" .env.local; then
    echo -e "${RED}❌ Placeholder 'replace-with-*' found in .env.local${NC}"
    placeholders_found=true
fi

if grep -q "your-key" .env.local; then
    echo -e "${RED}❌ Placeholder 'your-key' found in .env.local${NC}"
    placeholders_found=true
fi

if grep -q "sk-1234567890" .env.local; then
    echo -e "${RED}❌ Example API key 'sk-1234567890*' found in .env.local${NC}"
    placeholders_found=true
fi

# Check for required variables
required_vars=(
    "JWT_SECRET"
    "REDIS_URL"
)

missing_vars=false

for var in "${required_vars[@]}"; do
    if ! grep -q "^${var}=" .env.local; then
        echo -e "${RED}❌ Required variable missing: ${var}${NC}"
        missing_vars=true
    fi
done

# Check JWT secret strength
if grep -q "^JWT_SECRET=" .env.local; then
    jwt_secret=$(grep "^JWT_SECRET=" .env.local | cut -d'=' -f2)
    jwt_length=${#jwt_secret}
    
    if [ $jwt_length -lt 32 ]; then
        echo -e "${YELLOW}⚠️  WARNING: JWT_SECRET is too short (${jwt_length} chars, minimum 32 recommended)${NC}"
        echo "Generate a secure secret with:"
        echo "  openssl rand -base64 32"
    fi
fi

# Check Redis URL format
if grep -q "^REDIS_URL=" .env.local; then
    redis_url=$(grep "^REDIS_URL=" .env.local | cut -d'=' -f2)
    
    if [[ ! $redis_url =~ ^redis(s)?:// ]]; then
        echo -e "${RED}❌ Invalid REDIS_URL format (should start with redis:// or rediss://)${NC}"
        missing_vars=true
    fi
fi

# Final verdict
if [ "$placeholders_found" = true ] || [ "$missing_vars" = true ]; then
    echo -e "\n${RED}❌ Environment validation FAILED${NC}"
    echo "Please fix the issues above before deployment"
    exit 1
else
    echo -e "\n${GREEN}✅ Environment validation PASSED${NC}"
    echo "All required variables are set and valid"
    exit 0
fi