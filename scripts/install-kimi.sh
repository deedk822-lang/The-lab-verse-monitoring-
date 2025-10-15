#!/usr/bin/env bash
set -euo pipefail

# auto-load user placeholders
if [[ -f .env ]]; then
  # shellcheck disable=SC1091
  source .env
fi

# fail fast if any required key is still a placeholder
required_vars=(
  ALIBABA_CLOUD_ACCESS_KEY_ID
  ALIBABA_CLOUD_ACCESS_KEY_SECRET
  ECT_LICENSE
  MOONSHOT_API_KEY
  ZHIPU_API_KEY
)
for var in "${required_vars[@]}"; do
  # Use a default empty value to avoid unbound variable error
  if [[ "${!var:-}" == *"<<<"* ]] || [[ -z "${!var:-}" ]]; then
    echo "❌  $var is not set or still contains a placeholder in .env — please edit it first"
    exit 1
  fi
done

# ----- rest of original install-kimi.sh below -----
# Installation script for Kimi Instruct AI Project Manager

echo "🤖 Installing Kimi Instruct AI Project Manager..."
echo "===================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if optional OpenAI API key is set
if [ -z "${OPENAI_API_KEY:-}" ]; then
    echo -e "${YELLOW}⚠️  Optional OPENAI_API_KEY environment variable is not set${NC}"
else
    echo -e "${GREEN}✅ Optional OpenAI API key found${NC}"
fi

# Create necessary directories
echo -e "${BLUE}📁 Creating directories...${NC}"
mkdir -p kimi_workspace
mkdir -p logs

# Set permissions
chmod 755 kimi_workspace
chmod 755 logs

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed. Please install Docker first.${NC}"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}❌ Docker Compose is not installed. Please install Docker Compose first.${NC}"
    exit 1
fi

# Build Kimi Docker image
echo -e "${BLUE}🏗️  Building Kimi Docker image...${NC}"
if docker build -f Dockerfile.kimi -t labverse/kimi-manager:latest .; then
    echo -e "${GREEN}✅ Kimi Docker image built successfully${NC}"
else
    echo -e "${RED}❌ Failed to build Kimi Docker image${NC}"
    exit 1
fi

# Final success message
echo ""
echo -e "${GREEN}🎉 Kimi Instruct installation completed successfully!${NC}"
echo ""
echo -e "${BLUE}🚀 Next steps:${NC}"
echo -e "1. Ensure your .env file is populated."
echo -e "2. Start the stack: ${YELLOW}docker-compose up -d${NC}"
echo -e "3. Access Kimi dashboard: ${YELLOW}http://localhost:8084/dashboard${NC}"
echo ""
echo -e "${GREEN}🎯 Your monitoring stack now has an AI project manager!${NC}"