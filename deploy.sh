#!/bin/bash

###############################################################################
# Lab-Verse Complete Deployment Script
# Deploys all services with zero-downtime and full integration
###############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Banner
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║         Lab-Verse Monitoring System - Complete Deployment      ║"
echo "║                    Version 2.0.0                               ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Check prerequisites
log_info "Checking prerequisites..."

if ! command -v docker &> /dev/null; then
    log_error "Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    log_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

log_success "Prerequisites check passed"

# Check if .env file exists
if [ ! -f .env ]; then
    log_error ".env file not found!"
    log_info "Creating .env from template..."

    if [ -f .env.example ]; then
        cp .env.example .env
        log_warning "Please edit .env file with your actual configuration"
        exit 1
    else
        log_error ".env.example not found. Cannot create .env file."
        exit 1
    fi
fi

log_success ".env file found"

# Validate required environment variables
log_info "Validating environment configuration..."

source .env

required_vars=(
    "POSTGRES_PASSWORD"
    "GRAFANA_ADMIN_PASSWORD"
    "OPENAI_API_KEY"
    "ANTHROPIC_API_KEY"
    "CONTENT_CREATOR_API_KEY"
    "JWT_SECRET"
)

missing_vars=()

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        missing_vars+=("$var")
    fi
done

if [ ${#missing_vars[@]} -ne 0 ]; then
    log_error "Missing required environment variables:"
    for var in "${missing_vars[@]}"; do
        echo "  - $var"
    done
    exit 1
fi

log_success "Environment validation passed"

# Create necessary directories
log_info "Creating necessary directories..."

mkdir -p nginx/ssl
mkdir -p db/init
mkdir -p monitoring/prometheus
mkdir -p monitoring/grafana/dashboards
mkdir -p monitoring/grafana/datasources
mkdir -p logs

log_success "Directories created"

# Generate SSL certificates if not exists
if [ ! -f nginx/ssl/cert.pem ] || [ ! -f nginx/ssl/key.pem ]; then
    log_info "Generating self-signed SSL certificates for development..."

    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout nginx/ssl/key.pem \
        -out nginx/ssl/cert.pem \
        -subj "/CN=localhost" \
        &> /dev/null

    log_success "SSL certificates generated"
else
    log_info "SSL certificates already exist"
fi

# Stop existing services
log_info "Stopping existing services..."
docker-compose -f docker-compose.production.yml down --remove-orphans &> /dev/null || true
log_success "Existing services stopped"

# Build images
log_info "Building Docker images..."

docker-compose -f docker-compose.production.yml build --parallel

if [ $? -eq 0 ]; then
    log_success "Docker images built successfully"
else
    log_error "Docker build failed"
    exit 1
fi

# Start all services
log_info "Starting all services..."
docker-compose -f docker-compose.production.yml up -d

log_info "Waiting for services to become healthy..."

# Health checks with polling
log_info "Performing health checks..."
echo ""
echo "Health Check Results:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

failed_checks=0
services_to_check=$(docker-compose -f docker-compose.production.yml config --services)

for service in $services_to_check; do
    echo -n "  $service... "

    # Poll for health status
    for i in {1..30}; do
        health_status=$(docker-compose -f docker-compose.production.yml ps "$service" | grep "$service" | awk '{print $NF}')

        if [[ "$health_status" == "(healthy)" ]]; then
            echo -e "${GREEN}✓ Healthy${NC}"
            break
        elif [[ "$health_status" == "" ]]; then
            echo -e "${YELLOW}✓ No health check defined${NC}"
            break
        elif [[ "$health_status" == "(starting)" ]]; then
            sleep 5
        else
            echo -e "${RED}✗ Unhealthy ($health_status)${NC}"
            failed_checks=$((failed_checks + 1))
            break
        fi

        if [ $i -eq 30 ]; then
            echo -e "${RED}✗ Timed out waiting for service to become healthy${NC}"
            failed_checks=$((failed_checks + 1))
        fi
    done
done

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Display deployment summary
if [ $failed_checks -eq 0 ]; then
    log_success "======================================"
    log_success "  DEPLOYMENT COMPLETED SUCCESSFULLY"
    log_success "======================================"
    echo ""
    echo "🚀 Your Lab-Verse Monitoring System is now running!"
    echo ""
    echo "Access Points:"
    echo "  🌐 Web Dashboard:    https://localhost"
    echo "  📊 API Documentation: http://localhost/docs"
    echo "  📈 Grafana:          http://localhost:3002"
    echo "  📉 Prometheus:       http://localhost:9090"
    echo ""
    echo "Useful Commands:"
    echo "  📋 View logs:        docker-compose -f docker-compose.production.yml logs -f"
    echo "  🔍 Check status:     docker-compose -f docker-compose.production.yml ps"
    echo "  🛑 Stop services:    docker-compose -f docker-compose.production.yml down"
    echo "  🔄 Restart service:  docker-compose -f docker-compose.production.yml restart <service>"
    echo ""
    echo "Next Steps:"
    echo "  1. Configure webhook URLs in each platform (see WEBHOOK_SETUP.md)"
    echo "  2. Test integrations"
    echo "  3. Monitor logs for any issues"
    echo ""
else
    log_error "======================================"
    log_error "  DEPLOYMENT COMPLETED WITH WARNINGS"
    log_error "======================================"
    echo ""
    echo "⚠️  $failed_checks service(s) failed health checks"
    echo ""
    echo "Troubleshooting:"
    echo "  1. Check logs: docker-compose -f docker-compose.production.yml logs"
    echo "  2. Verify .env configuration"
    echo "  3. Check port availability"
    echo ""
fi

log_info "Deployment script completed!"
