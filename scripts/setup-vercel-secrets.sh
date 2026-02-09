#!/bin/bash

# Vercel Secrets Setup Script
# This script helps you configure all required secrets in Vercel

set -e

echo "=================================="
echo "VERCEL SECRETS CONFIGURATION"
echo "=================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Check if Vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo -e "${RED}✗${NC} Vercel CLI not found"
    echo ""
    echo "Install Vercel CLI:"
    echo "  npm install -g vercel"
    echo ""
    exit 1
fi

echo -e "${GREEN}✓${NC} Vercel CLI found"
echo ""

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠${NC} No .env file found"
    echo "Please create a .env file with your API keys first"
    echo "You can copy from .env.example:"
    echo "  cp .env.example .env"
    echo ""
    exit 1
fi

echo -e "${GREEN}✓${NC} .env file found"
echo ""

# Function to add secret to Vercel
add_secret() {
    local key=$1
    local value=$2
    local secret_name=$(echo "$key" | tr '[:upper:]' '[:lower:]')

    if [ -z "$value" ] || [ "$value" = "your_"*"_here" ]; then
        echo -e "${YELLOW}⊘${NC} Skipping $key (not configured)"
        return
    fi

    echo "Adding secret: $secret_name"
    echo "$value" | vercel secrets add "$secret_name" 2>/dev/null || {
        # Secret might already exist, try to remove and re-add
        vercel secrets rm "$secret_name" -y 2>/dev/null || true
        echo "$value" | vercel secrets add "$secret_name"
    }
    echo -e "${GREEN}✓${NC} $key configured"
}

# Required secrets
echo "Configuring required secrets..."
echo ""

# Load .env file
export $(cat .env | grep -v '^#' | xargs)

# AI Providers (at least one required)
echo "=== AI Providers ==="
add_secret "COHERE_API_KEY" "${COHERE_API_KEY}"
add_secret "GROQ_API_KEY" "${GROQ_API_KEY}"
add_secret "OPENAI_API_KEY" "${OPENAI_API_KEY}"
add_secret "ANTHROPIC_API_KEY" "${ANTHROPIC_API_KEY}"
add_secret "HUGGINGFACE_TOKEN" "${HUGGINGFACE_TOKEN}"
echo ""

# Optional AI Providers
echo "=== Optional AI Providers ==="
add_secret "GOOGLE_AI_API_KEY" "${GOOGLE_AI_API_KEY}"
add_secret "MISTRAL_API_KEY" "${MISTRAL_API_KEY}"
# GLM4 is optional - only add if configured
if [ ! -z "${GLM4_API_KEY}" ] && [ "${GLM4_API_KEY}" != "your_glm4_key_here" ]; then
    add_secret "GLM4_API_KEY" "${GLM4_API_KEY}"
fi
echo ""

# Local AI
echo "=== Local AI ==="
add_secret "LOCALAI_BASE_URL" "${LOCALAI_BASE_URL}"
echo ""

# Image Generation
echo "=== Image Generation ==="
add_secret "STABILITY_API_KEY" "${STABILITY_API_KEY}"
add_secret "REPLICATE_API_TOKEN" "${REPLICATE_API_TOKEN}"
echo ""

# Communication
echo "=== Communication ==="
add_secret "TWILIO_ACCOUNT_SID" "${TWILIO_ACCOUNT_SID}"
add_secret "TWILIO_AUTH_TOKEN" "${TWILIO_AUTH_TOKEN}"
echo ""

# Social Media
echo "=== Social Media ==="
add_secret "AYRSHARE_API_KEY" "${AYRSHARE_API_KEY}"
add_secret "SOCIALPILOT_API_KEY" "${SOCIALPILOT_API_KEY}"
add_secret "TWITTER_API_KEY" "${TWITTER_API_KEY}"
add_secret "TWITTER_API_SECRET" "${TWITTER_API_SECRET}"
add_secret "TWITTER_ACCESS_TOKEN" "${TWITTER_ACCESS_TOKEN}"
add_secret "TWITTER_ACCESS_TOKEN_SECRET" "${TWITTER_ACCESS_TOKEN_SECRET}"
add_secret "TWITTER_BEARER_TOKEN" "${TWITTER_BEARER_TOKEN}"
add_secret "FACEBOOK_PAGE_ACCESS_TOKEN" "${FACEBOOK_PAGE_ACCESS_TOKEN}"
add_secret "FACEBOOK_PAGE_ID" "${FACEBOOK_PAGE_ID}"
echo ""

# Email & Marketing
echo "=== Email & Marketing ==="
add_secret "MAILCHIMP_API_KEY" "${MAILCHIMP_API_KEY}"
echo ""

# Project Management
echo "=== Project Management ==="
add_secret "ASANA_ACCESS_TOKEN" "${ASANA_ACCESS_TOKEN}"
add_secret "JIRA_API_TOKEN" "${JIRA_API_TOKEN}"
echo ""

# Security
echo "=== Security ==="
add_secret "SECRET_KEY" "${SECRET_KEY}"
add_secret "API_KEY" "${API_KEY}"
add_secret "JWT_SECRET" "${JWT_SECRET}"
echo ""

echo "=================================="
echo "CONFIGURATION COMPLETE"
echo "=================================="
echo ""
echo "Next steps:"
echo "1. Link your project: vercel link"
echo "2. Deploy: vercel --prod"
echo ""
echo "To update environment variables in Vercel dashboard:"
echo "1. Go to https://vercel.com/dashboard"
echo "2. Select your project"
echo "3. Go to Settings > Environment Variables"
echo "4. Add any missing variables"
echo ""
echo -e "${GREEN}✓${NC} Setup complete!"