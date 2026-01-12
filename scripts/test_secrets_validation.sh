#!/bin/bash
set -e

echo "🔐 Vaal AI Empire - Secret Validation Test"
echo "=========================================="
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

MISSING_SECRETS=()
VALIDATED_SECRETS=()

# Function to check if secret exists
check_secret() {
    local secret_name=$1
    local secret_value=$2

    if [ -z "$secret_value" ]; then
        echo -e "${RED}✗${NC} $secret_name - MISSING"
        MISSING_SECRETS+=("$secret_name")
    else
        echo -e "${GREEN}✓${NC} $secret_name - Present"
        VALIDATED_SECRETS+=("$secret_name")
    fi
}

echo "Testing Core Secrets..."
echo "----------------------"

# AI Model APIs
check_secret "DASHSCOPE_API_KEY" "$DASHSCOPE_API_KEY"
check_secret "COHERE_API_KEY" "$COHERE_API_KEY"
check_secret "MISTRALAI_API_KEY" "$MISTRALAI_API_KEY"
check_secret "OPENAI_API_KEY" "$OPENAI_API_KEY"

# Data Sources
check_secret "NOTION_API_KEY" "$NOTION_API_KEY"
check_secret "KAGGLE_USERNAME" "$KAGGLE_USERNAME"
check_secret "KAGGLE_API_KEY" "$KAGGLE_API_KEY"

# Publishing Platforms
check_secret "WORDPRESS_USER" "$WORDPRESS_USER"
check_secret "WORDPRESS_PASSWORD" "$WORDPRESS_PASSWORD"
check_secret "JIRA_USER_EMAIL" "$JIRA_USER_EMAIL"
check_secret "JIRA_LINK" "$JIRA_LINK"

# Marketing Tools
check_secret "ARYSHARE_API_KEY" "$ARYSHARE_API_KEY"
check_secret "MAILCHIMP_API_KEY" "$MAILCHIMP_API_KEY"

# Storage
check_secret "ACCESS_KEY_ID" "$ACCESS_KEY_ID"
check_secret "ACCESS_KEY_SECRET" "$ACCESS_KEY_SECRET"

# Databricks
check_secret "DATABRICKS_HOST" "$DATABRICKS_HOST"
check_secret "DATABRICKS_API_KEY" "$DATABRICKS_API_KEY"

echo ""
echo "Summary"
echo "-------"
echo -e "${GREEN}✓ Validated: ${#VALIDATED_SECRETS[@]}${NC}"
echo -e "${RED}✗ Missing: ${#MISSING_SECRETS[@]}${NC}"

if [ ${#MISSING_SECRETS[@]} -gt 0 ]; then
    echo ""
    echo -e "${YELLOW}Missing Secrets:${NC}"
    for secret in "${MISSING_SECRETS[@]}"; do
        echo "  - $secret"
    done
    echo ""
    echo "⚠️  Configure missing secrets in GitHub Settings → Secrets and variables → Actions"
    exit 1
fi

echo ""
echo -e "${GREEN}✓ All secrets validated successfully!${NC}"
exit 0
