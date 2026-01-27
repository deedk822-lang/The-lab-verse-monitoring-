# Forced change to resolve conflicts and ensure push success
#!/bin/bash
# ============================================================================
# VAAL AI Empire - Agent Setup Script
# ============================================================================

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
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

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        log_warning "This script should not be run as root. Running as regular user."
    fi
}

# Check system requirements
check_requirements() {
    log_info "Checking system requirements..."

    # Check Python version
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
        log_success "Python $PYTHON_VERSION found"
    else
        log_error "Python 3 not found. Please install Python 3.10 or higher."
        exit 1
    fi

    # Check CUDA availability (optional)
    if command -v nvidia-smi &> /dev/null; then
        log_success "NVIDIA GPU detected"
        nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader
    else
        log_warning "No NVIDIA GPU detected. Will use CPU mode."
    fi

    # Check Docker
    if command -v docker &> /dev/null; then
        log_success "Docker $(docker --version | cut -d' ' -f3) found"
    else
        log_warning "Docker not found. Some features may not be available."
    fi

    # Check Docker Compose
    if command -v docker-compose &> /dev/null; then
        log_success "Docker Compose $(docker-compose --version | cut -d' ' -f4) found"
    else
        log_warning "Docker Compose not found."
    fi
}

# Create directory structure
create_directories() {
    log_info "Creating directory structure..."

    mkdir -p \
        models \
        cache/huggingface \
        logs \
        uploads \
        backups \
        nginx/ssl \
        monitoring/grafana/{dashboards,datasources} \
        vaal_ai_empire/api \
        agent/{tools,nodes}

    log_success "Directory structure created"
}

# Setup Python virtual environment
setup_venv() {
    log_info "Setting up Python virtual environment..."

    if [[ ! -d "venv" ]]; then
        python3 -m venv venv
        log_success "Virtual environment created"
    else
        log_info "Virtual environment already exists"
    fi

    # Activate virtual environment
    source venv/bin/activate

    # Upgrade pip
    pip install --upgrade pip setuptools wheel

    log_success "Virtual environment ready"
}

# Install Python dependencies
install_dependencies() {
    log_info "Installing Python dependencies..."

    if [[ -f "requirements.txt" ]]; then
        pip install -r requirements.txt
        log_success "Dependencies installed"
    else
        log_error "requirements.txt not found"
        exit 1
    fi

    # Install development dependencies if requested
    if [[ "${INSTALL_DEV:-false}" == "true" ]] && [[ -f "requirements-dev.txt" ]]; then
        log_info "Installing development dependencies..."
        pip install -r requirements-dev.txt
        log_success "Development dependencies installed"
    fi
}

# Setup environment configuration
setup_env() {
    log_info "Setting up environment configuration..."

    if [[ ! -f ".env" ]]; then
        if [[ -f ".env.example" ]]; then
            cp .env.example .env
            log_warning "Created .env from .env.example. Please update with your values."
        else
            log_error ".env.example not found"
            exit 1
        fi
    else
        log_info ".env file already exists"
    fi

    # Generate random secrets if not set
    if ! grep -q "SECRET_KEY=" .env || grep -q "your-secret-key-change-this" .env; then
        NEW_SECRET=$(openssl rand -hex 32)
        if [[ "$OSTYPE" == "darwin"* ]]; then
            sed -i '' "s/SECRET_KEY=.*/SECRET_KEY=$NEW_SECRET/" .env
        else
            sed -i "s/SECRET_KEY=.*/SECRET_KEY=$NEW_SECRET/" .env
        fi
        log_success "Generated new SECRET_KEY"
    fi

    if ! grep -q "JWT_SECRET_KEY=" .env || grep -q "your-jwt-secret-change-this" .env; then
        NEW_JWT_SECRET=$(openssl rand -hex 32)
        if [[ "$OSTYPE" == "darwin"* ]]; then
            sed -i '' "s/JWT_SECRET_KEY=.*/JWT_SECRET_KEY=$NEW_JWT_SECRET/" .env
        else
            sed -i "s/JWT_SECRET_KEY=.*/JWT_SECRET_KEY=$NEW_JWT_SECRET/" .env
        fi
        log_success "Generated new JWT_SECRET_KEY"
    fi
}

# Initialize database
init_database() {
    log_info "Initializing database..."

    # Check if DATABASE_URL is set
    if grep -q "DATABASE_URL" .env; then
        log_info "Running database migrations..."

        # Using Docker Compose
        if command -v docker-compose &> /dev/null && [[ -f "docker-compose.yml" ]]; then
            docker-compose up -d postgres
            sleep 5

            # Run migrations
            docker-compose exec -T postgres psql -U vaaluser -d vaal_ai_empire -f /docker-entrypoint-initdb.d/init.sql || true

            log_success "Database initialized"
        else
            log_warning "Docker Compose not available. Please run migrations manually."
        fi
    else
        log_warning "DATABASE_URL not configured. Skipping database initialization."
    fi
}

# Download models (optional)
download_models() {
    if [[ "${DOWNLOAD_MODELS:-false}" == "true" ]]; then
        log_info "Downloading AI models..."

        # Check if HuggingFace token is set
        if grep -q "HF_TOKEN=" .env && ! grep -q "your-huggingface-token" .env; then
            source .env

            # Download default model
            python3 - <<EOF
from huggingface_hub import snapshot_download
import os

model_id = os.getenv('HF_DEFAULT_MODEL', 'meta-llama/Llama-3.2-3B-Instruct')
cache_dir = os.getenv('HF_CACHE_DIR', './cache/huggingface')

print(f"Downloading {model_id}...")
snapshot_download(model_id, cache_dir=cache_dir)
print("Model downloaded successfully")
EOF
            log_success "Models downloaded"
        else
            log_warning "HF_TOKEN not configured. Skipping model download."
        fi
    fi
}

# Run tests
run_tests() {
    if [[ "${RUN_TESTS:-false}" == "true" ]]; then
        log_info "Running tests..."

        if command -v pytest &> /dev/null; then
            pytest tests/ -v --cov=vaal_ai_empire --cov-report=html
            log_success "Tests completed"
        else
            log_warning "pytest not installed. Skipping tests."
        fi
    fi
}

# Setup monitoring
setup_monitoring() {
    if [[ "${SETUP_MONITORING:-false}" == "true" ]]; then
        log_info "Setting up monitoring..."

        # Create Prometheus config
        cat > monitoring/prometheus.yml <<EOF
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'vaal-app'
    static_configs:
      - targets: ['app:9090']

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres:5432']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']
EOF

        log_success "Monitoring configured"
    fi
}

# Display completion message
completion_message() {
    log_success "Setup completed successfully!"
    echo ""
    echo "Next steps:"
    echo "1. Review and update .env with your configuration"
    echo "2. Start the application:"
    echo "   - Development: source venv/bin/activate && uvicorn app.main:app --reload"
    echo "   - Production: docker-compose up -d"
    echo "3. Access the application at http://localhost:8000"
    echo "4. Check health: curl http://localhost:8000/health"
    echo ""
    echo "Optional services:"
    echo "- Grafana dashboard: http://localhost:3000"
    echo "- Prometheus metrics: http://localhost:9091"
    echo "- pgAdmin: docker-compose --profile tools up -d pgadmin"
    echo ""
}

# Main setup flow
main() {
    echo "============================================"
    echo "VAAL AI Empire - Setup Script"
    echo "============================================"
    echo ""

    check_root
    check_requirements
    create_directories
    setup_venv
    install_dependencies
    setup_env
    init_database
    download_models
    setup_monitoring
    run_tests
    completion_message
}

# Run main function
main "$@"
