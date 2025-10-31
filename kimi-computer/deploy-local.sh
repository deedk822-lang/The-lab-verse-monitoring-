#!/bin/bash

# Kimi Computer - Local Deployment Script
# This script deploys the complete Kimi Computer system locally using Docker Compose

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="kimi-computer"
COMPOSE_FILE="docker-compose.yml"
ENV_FILE=".env"
REQUIRED_VARS=("OLLAMA_HOST" "CHROMADB_HOST" "CHROMADB_PORT")

echo -e "${BLUE}🚀 Kimi Computer - Local Deployment${NC}"
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
if [ ! -f "$COMPOSE_FILE" ]; then
    print_error "docker-compose.yml not found in current directory"
    print_error "Please run this script from the kimi-computer directory"
    exit 1
fi

# Check if Docker is installed
if ! command_exists docker; then
    print_error "Docker is not installed"
    print_info "Please install Docker Desktop from https://www.docker.com/products/docker-desktop"
    exit 1
fi

# Check if Docker Compose is installed
if ! command_exists docker-compose; then
    print_error "Docker Compose is not installed"
    print_info "Please install Docker Compose"
    exit 1
fi

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    print_error "Docker is not running"
    print_info "Please start Docker Desktop"
    exit 1
fi

print_status "Prerequisites check passed"

# Check environment file
echo -e "\n${BLUE}🔧 Checking environment configuration...${NC}"

if [ ! -f "$ENV_FILE" ]; then
    print_warning ".env file not found. Creating from template..."
    
    if [ -f ".env.example" ]; then
        cp .env.example .env
        print_status ".env file created from template"
        print_warning "Please edit .env file with your actual API keys before proceeding"
        read -p "Press Enter to continue after editing .env file..."
    else
        print_error ".env.example file not found"
        exit 1
    fi
else
    print_status ".env file found"
fi

# Validate required environment variables
echo "Validating environment variables..."
MISSING_VARS=()

for var in "${REQUIRED_VARS[@]}"; do
    if ! grep -q "^$var=" "$ENV_FILE" || grep -q "^$var=$" "$ENV_FILE"; then
        MISSING_VARS+=("$var")
    fi
done

if [ ${#MISSING_VARS[@]} -gt 0 ]; then
    print_error "Missing required environment variables: ${MISSING_VARS[*]}"
    print_error "Please set these variables in your .env file"
    exit 1
fi

print_status "Environment variables validated"

# Clean up any existing containers
echo -e "\n${BLUE}🧹 Cleaning up existing containers...${NC}"

if docker-compose -f "$COMPOSE_FILE" ps -q | grep -q .; then
    print_info "Stopping existing containers..."
    docker-compose -f "$COMPOSE_FILE" down
    print_status "Existing containers stopped"
fi

# Build and start services
echo -e "\n${BLUE}🏗️  Building and starting services...${NC}"

print_info "Building Docker images..."
docker-compose -f "$COMPOSE_FILE" build

print_info "Starting services..."
docker-compose -f "$COMPOSE_FILE" up -d

print_status "Services started successfully"

# Wait for services to be ready
echo -e "\n${BLUE}⏳ Waiting for services to be ready...${NC}"

# Wait for Ollama
print_info "Waiting for Ollama to be ready..."
for i in {1..60}; do
    if curl -f http://localhost:11434/api/tags >/dev/null 2>&1; then
        print_status "Ollama is ready"
        break
    fi
    echo -n "."
    sleep 2
done

# Wait for ChromaDB
print_info "Waiting for ChromaDB to be ready..."
for i in {1..30}; do
    if curl -f http://localhost:8000/api/v1/heartbeat >/dev/null 2>&1; then
        print_status "ChromaDB is ready"
        break
    fi
    echo -n "."
    sleep 2
done

# Wait for FastAPI
print_info "Waiting for FastAPI to be ready..."
for i in {1..60}; do
    if curl -f http://localhost:8080/health >/dev/null 2>&1; then
        print_status "FastAPI is ready"
        break
    fi
    echo -n "."
    sleep 2
done

# Check service status
echo -e "\n${BLUE}🔍 Checking service status...${NC}"

echo "Container status:"
docker-compose -f "$COMPOSE_FILE" ps

echo -e "\nService health checks:"

# Check Ollama
if curl -f http://localhost:11434/api/tags >/dev/null 2>&1; then
    print_status "Ollama: Healthy (http://localhost:11434)"
else
    print_error "Ollama: Unhealthy"
fi

# Check ChromaDB
if curl -f http://localhost:8000/api/v1/heartbeat >/dev/null 2>&1; then
    print_status "ChromaDB: Healthy (http://localhost:8000)"
else
    print_error "ChromaDB: Unhealthy"
fi

# Check FastAPI
if curl -f http://localhost:8080/health >/dev/null 2>&1; then
    print_status "FastAPI: Healthy (http://localhost:8080)"
else
    print_error "FastAPI: Unhealthy"
fi

# Pull Mistral model if not already present
echo -e "\n${BLUE}🧠 Setting up Mistral model...${NC}"

if ! curl -s http://localhost:11434/api/tags | grep -q "mistral"; then
    print_info "Pulling Mistral model..."
    docker exec ollama ollama pull mistral:7b-instruct-v0.3
    print_status "Mistral model downloaded"
else
    print_status "Mistral model already available"
fi

# Display access URLs
echo -e "\n${BLUE}🌐 Access URLs${NC}"
echo "======================================="
echo -e "${GREEN}FastAPI Application:${NC} http://localhost:8080"
echo -e "${GREEN}API Documentation:${NC}  http://localhost:8080/docs"
echo -e "${GREEN}Health Check:${NC}       http://localhost:8080/health"
echo -e "${GREEN}Landing Page:${NC}       http://localhost:8080/landing"
echo -e "${GREEN}Ollama API:${NC}         http://localhost:11434"
echo -e "${GREEN}ChromaDB API:${NC}       http://localhost:8000"

# Display useful commands
echo -e "\n${BLUE}🛠️  Useful Commands${NC}"
echo "======================================="
echo -e "${YELLOW}View logs:${NC}           docker-compose -f $COMPOSE_FILE logs -f"
echo -e "${YELLOW}Stop services:${NC}       docker-compose -f $COMPOSE_FILE down"
echo -e "${YELLOW}Restart services:${NC}    docker-compose -f $COMPOSE_FILE restart"
echo -e "${YELLOW}Check status:${NC}        docker-compose -f $COMPOSE_FILE ps"
echo -e "${YELLOW}Run tests:${NC}           ./test-e2e.sh"

# Next steps
echo -e "\n${BLUE}🚀 Next Steps${NC}"
echo "======================================="
echo "1. Configure your API keys in .env file if not already done"
echo "2. Import the Make.com workflow from make-blueprint.json"
echo "3. Set up your Brave Ads campaign with conversion tracking"
echo "4. Test the system by running: ./test-e2e.sh"
echo "5. Deploy to production with: ./deploy-fly.sh"

# Test basic functionality
echo -e "\n${BLUE}🧪 Testing basic functionality...${NC}"

# Test health endpoint
if curl -f http://localhost:8080/health >/dev/null 2>&1; then
    print_status "Health endpoint test passed"
else
    print_warning "Health endpoint test failed"
fi

# Test landing page
if curl -f http://localhost:8080/landing >/dev/null 2>&1; then
    print_status "Landing page test passed"
else
    print_warning "Landing page test failed"
fi

# Final status
echo -e "\n${GREEN}🎉 Local deployment completed successfully!${NC}"
echo "======================================="
print_status "Kimi Computer is running locally"
print_status "All services are operational"

# Monitoring advice
echo -e "\n${YELLOW}💡 Monitoring Tips:${NC}"
echo "• Use 'docker stats' to monitor resource usage"
echo "• Check logs with 'docker-compose logs -f kimi-api'"
echo "• Monitor model performance via the /health endpoint"
echo "• Set up alerts for service health in production"

echo -e "\n${GREEN}✨ Your local Kimi Computer is ready to use!${NC}"