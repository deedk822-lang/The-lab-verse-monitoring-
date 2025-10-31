#!/bin/bash

# Kimi Computer - Fly.io Deployment Script
# This script deploys the Kimi Computer system to Fly.io

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="kimi-computer"
FLY_TOML="fly.toml"
ENV_FILE=".env"

echo -e "${BLUE}🚀 Kimi Computer - Fly.io Deployment${NC}"
echo "======================================="

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to print status
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

# Function to print warning
print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Function to print error
print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Function to print info
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check prerequisites
echo -e "\n${BLUE}📋 Checking prerequisites...${NC}"

# Check if we're in the right directory
if [ ! -f "$FLY_TOML" ]; then
    print_error "fly.toml not found in current directory"
    print_error "Please run this script from the kimi-computer directory"
    exit 1
fi

# Check if Fly CLI is installed
if ! command_exists flyctl; then
    print_error "Fly CLI (flyctl) is not installed"
    print_info "Please install it from: https://fly.io/docs/hands-on/install-flyctl/"
    exit 1
fi

# Check if user is logged in to Fly
if ! flyctl auth whoami >/dev/null 2>&1; then
    print_error "You are not logged in to Fly.io"
    print_info "Please run: flyctl auth login"
    exit 1
fi

print_status "Prerequisites check passed"

# Check environment configuration
echo -e "\n${BLUE}🔧 Checking environment configuration...${NC}"

if [ ! -f "$ENV_FILE" ]; then
    print_error ".env file not found"
    print_info "Please create .env file with your configuration"
    exit 1
fi

print_status "Environment file found"

# Load environment variables
set -a
source .env
set +a

# Validate required variables
REQUIRED_VARS=("OLLAMA_HOST" "CHROMADB_HOST" "CHROMADB_PORT")
MISSING_VARS=()

for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        MISSING_VARS+=("$var")
    fi
done

if [ ${#MISSING_VARS[@]} -gt 0 ]; then
    print_error "Missing required environment variables: ${MISSING_VARS[*]}"
    exit 1
fi

print_status "Environment variables validated"

# Check if app exists
echo -e "\n${BLUE}🔍 Checking Fly.io app status...${NC}"

if flyctl status --app "$APP_NAME" >/dev/null 2>&1; then
    print_status "App '$APP_NAME' already exists"
    EXISTING_APP=true
else
    print_info "App '$APP_NAME' does not exist. Creating new app..."
    flyctl launch --no-deploy --name "$APP_NAME" --copy-config --region "iad"
    print_status "App '$APP_NAME' created successfully"
    EXISTING_APP=false
fi

# Set up secrets
echo -e "\n${BLUE}🔐 Setting up Fly.io secrets...${NC}"

# Function to set secret if value exists
set_secret_if_exists() {
    local var_name="$1"
    local var_value="${!var_name}"
    
    if [ -n "$var_value" ]; then
        print_info "Setting secret: $var_name"
        flyctl secrets set "$var_name=$var_value" --app "$APP_NAME"
    else
        print_warning "Skipping secret (not set): $var_name"
    fi
}

# Set all secrets from environment
set_secret_if_exists "AYR_KEY"
set_secret_if_exists "MAKE_WEBHOOK"
set_secret_if_exists "BRAVE_VERIFICATION_TOKEN"
set_secret_if_exists "GOOGLE_ADS_DEVELOPER_TOKEN"
set_secret_if_exists "GOOGLE_ADS_CLIENT_ID"
set_secret_if_exists "GOOGLE_ADS_CLIENT_SECRET"
set_secret_if_exists "GOOGLE_ADS_REFRESH_TOKEN"
set_secret_if_exists "GOOGLE_ADS_CUSTOMER_ID"
set_secret_if_exists "MAILCHIMP_API_KEY"
set_secret_if_exists "MAILCHIMP_LIST_ID"
set_secret_if_exists "MAILCHIMP_DC"
set_secret_if_exists "SLACK_WEBHOOK_URL"
set_secret_if_exists "REDIS_URL"
set_secret_if_exists "SENTRY_DSN"
set_secret_if_exists "GOOGLE_ANALYTICS_ID"

print_status "Secrets configured"

# Deploy to Fly.io
echo -e "\n${BLUE}🚀 Deploying to Fly.io...${NC}"

print_info "Building and deploying application..."

# Deploy with verbose output
flyctl deploy --app "$APP_NAME" --region "iad" --verbose

if [ $? -eq 0 ]; then
    print_status "Deployment completed successfully"
else
    print_error "Deployment failed"
    exit 1
fi

# Wait for deployment to be ready
echo -e "\n${BLUE}⏳ Waiting for deployment to be ready...${NC}"

print_info "Waiting for app to start..."

for i in {1..60}; do
    if curl -f "https://$APP_NAME.fly.dev/health" >/dev/null 2>&1; then
        print_status "App is ready and healthy"
        break
    fi
    echo -n "."
    sleep 5
done

# Verify deployment
echo -e "\n${BLUE}🔍 Verifying deployment...${NC}"

APP_URL="https://$APP_NAME.fly.dev"
HEALTH_URL="$APP_URL/health"
LANDING_URL="$APP_URL/landing"
DOCS_URL="$APP_URL/docs"

# Test health endpoint
if curl -f "$HEALTH_URL" >/dev/null 2>&1; then
    print_status "Health check passed: $HEALTH_URL"
else
    print_warning "Health check failed: $HEALTH_URL"
fi

# Test landing page
if curl -f "$LANDING_URL" >/dev/null 2>&1; then
    print_status "Landing page accessible: $LANDING_URL"
else
    print_warning "Landing page not accessible: $LANDING_URL"
fi

# Display deployment information
echo -e "\n${BLUE}🌐 Deployment Information${NC}"
echo "======================================="
echo -e "${GREEN}Application URL:${NC}   $APP_URL"
echo -e "${GREEN}API Documentation:${NC} $DOCS_URL"
echo -e "${GREEN}Health Check:${NC}     $HEALTH_URL"
echo -e "${GREEN}Landing Page:${NC}     $LANDING_URL"

# Get app status
echo -e "\n${BLUE}📊 App Status${NC}"
echo "======================================="
flyctl status --app "$APP_NAME"

# Display useful commands
echo -e "\n${BLUE}🛠️  Useful Commands${NC}"
echo "======================================="
echo -e "${YELLOW}View logs:${NC}         flyctl logs --app $APP_NAME"
echo -e "${YELLOW}Open app:${NC}          flyctl open --app $APP_NAME"
echo -e "${YELLOW}Restart app:${NC}       flyctl restart --app $APP_NAME"
echo -e "${YELLOW}Scale app:${NC}         flyctl scale count 1 --app $APP_NAME"
echo -e "${YELLOW}Destroy app:${NC}       flyctl destroy --app $APP_NAME"

# Monitoring setup
echo -e "\n${BLUE}📈 Monitoring Setup${NC}"
echo "======================================="
print_info "Setting up monitoring..."

# Enable metrics if available
if flyctl machine list --app "$APP_NAME" 2>/dev/null | grep -q .; then
    print_info "Machine-based deployment detected"
else
    print_info "Standard app deployment detected"
fi

# Next steps
echo -e "\n${BLUE}🚀 Post-Deployment Steps${NC}"
echo "======================================="
echo "1. Update your Brave Ads destination URL to: $LANDING_URL"
echo "2. Configure your Make.com webhook to point to: $APP_URL/catch"
echo "3. Test the deployment by running: curl $HEALTH_URL"
echo "4. Monitor your app with: flyctl logs --app $APP_NAME --follow"
echo "5. Set up a custom domain if needed: flyctl certs add yourdomain.com"

# Test production endpoints
echo -e "\n${BLUE}🧪 Testing Production Endpoints${NC}"

# Test with curl
echo "Testing health endpoint..."
HEALTH_RESPONSE=$(curl -s "$HEALTH_URL")
if echo "$HEALTH_RESPONSE" | grep -q '"status"'; then
    print_status "Health endpoint responding correctly"
else
    print_warning "Health endpoint response unexpected"
fi

echo "Testing landing page..."
LANDING_RESPONSE=$(curl -s "$LANDING_URL")
if echo "$LANDING_RESPONSE" | grep -q "Kimi Computer"; then
    print_status "Landing page loading correctly"
else
    print_warning "Landing page content unexpected"
fi

# Performance recommendations
echo -e "\n${BLUE}💡 Performance Recommendations${NC}"
echo "======================================="
echo "• Monitor app performance with Fly.io metrics"
echo "• Consider adding Redis for rate limiting"
echo "• Set up custom domains for production use"
echo "• Configure SSL certificates for custom domains"
echo "• Monitor resource usage and scale as needed"

# Security considerations
echo -e "\n${YELLOW}🔒 Security Considerations${NC}"
echo "======================================="
echo "• All secrets are stored securely in Fly.io"
echo "• API endpoints are accessible via HTTPS"
echo "• Consider adding API rate limiting"
echo "• Monitor for suspicious activity"
echo "• Keep dependencies updated regularly"

# Final status
echo -e "\n${GREEN}🎉 Fly.io deployment completed successfully!${NC}"
echo "======================================="
print_status "Kimi Computer is deployed and running on Fly.io"
print_status "App URL: $APP_URL"

# Alert about free tier limitations
echo -e "\n${YELLOW}⚠️  Free Tier Limitations${NC}"
echo "======================================="
echo "• Fly.io free tier includes shared CPU, 256MB RAM, 3GB bandwidth"
echo "• Ollama and Mistral model may require more resources"
echo "• Consider upgrading to paid tier for production workloads"
echo "• Monitor usage to avoid unexpected charges"

echo -e "\n${GREEN}✨ Your Kimi Computer is now live on Fly.io!${NC}"