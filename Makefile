# Makefile for LabVerse Monitoring Stack with Kimi Instruct

# Colors
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[1;33m
BLUE := \033[0;34m
NC := \033[0m # No Color

# Default target
.DEFAULT_GOAL := help

## Main Stack Operations

# Install all dependencies
install: ## Install all Python dependencies
	@echo -e "$(BLUE)📦 Installing dependencies...$(NC)"
	pip install -r requirements.txt
	pip install -r requirements.kimi.txt
	@echo -e "$(GREEN)✅ Dependencies installed$(NC)"

# Build all Docker images
build: ## Build all Docker images (cost optimizer, Kimi)
	@echo -e "$(BLUE)🏗️  Building Docker images...$(NC)"
	docker build -t labverse/cost-optimizer:latest -f Dockerfile.cost-optimizer .
	docker build -t labverse/kimi-manager:latest -f Dockerfile.kimi .
	@echo -e "$(GREEN)✅ All images built successfully$(NC)"

# Start the entire stack
up: ## Start the complete monitoring stack with Kimi
	@echo -e "$(BLUE)🚀 Starting LabVerse monitoring stack...$(NC)"
	docker-compose up -d
	@echo -e "$(GREEN)✅ Stack is running!$(NC)"
	@echo -e "$(BLUE)Access points:$(NC)"
	@echo -e "  • Kimi Dashboard: http://localhost:8084/dashboard"
	@echo -e "  • Prometheus: http://localhost:9090"
	@echo -e "  • Grafana: http://localhost:3000"
	@echo -e "  • AlertManager: http://localhost:9093"

# Stop the entire stack
down: ## Stop the complete monitoring stack
	@echo -e "$(YELLOW)🛋 Stopping LabVerse monitoring stack...$(NC)"
	docker-compose down
	@echo -e "$(GREEN)✅ Stack stopped$(NC)"

# Restart the stack
restart: down up ## Restart the complete stack

## Kimi Instruct Operations

# Install Kimi Instruct
install-kimi: ## Install Kimi Instruct AI Project Manager
	@echo -e "$(BLUE)🤖 Installing Kimi Instruct...$(NC)"
	./scripts/install-kimi.sh

# Start only Kimi service
kimi-up: ## Start only the Kimi Instruct service
	@echo -e "$(BLUE)🤖 Starting Kimi Instruct...$(NC)"
	docker-compose up -d kimi-project-manager
	@echo -e "$(GREEN)✅ Kimi is running at http://localhost:8084/dashboard$(NC)"

# Stop only Kimi service
kimi-down: ## Stop the Kimi Instruct service
	@echo -e "$(YELLOW)🛋 Stopping Kimi Instruct...$(NC)"
	docker-compose stop kimi-project-manager

# Restart Kimi service
kimi-restart: kimi-down kimi-up ## Restart Kimi Instruct service

# View Kimi logs
kimi-logs: ## View Kimi Instruct logs
	@echo -e "$(BLUE)📄 Kimi Instruct logs:$(NC)"
	docker-compose logs -f kimi-project-manager

# Check Kimi status
kimi-status: ## Check Kimi Instruct status
	@echo -e "$(BLUE)🔍 Checking Kimi status...$(NC)"
	./check-kimi

# Open Kimi dashboard
kimi-dashboard: ## Open Kimi dashboard in browser
	@echo -e "$(BLUE)📊 Opening Kimi dashboard...$(NC)"
	@which xdg-open > /dev/null && xdg-open http://localhost:8084/dashboard || \
	 which open > /dev/null && open http://localhost:8084/dashboard || \
	 echo -e "$(YELLOW)Please open http://localhost:8084/dashboard in your browser$(NC)"

## CLI Operations

# Kimi CLI status
status: ## Show project status via Kimi CLI
	@echo -e "$(BLUE)🎯 Getting project status...$(NC)"
	./kimi-cli status

# Create a task via CLI
task: ## Create a task (usage: make task TITLE="Task name" PRIORITY=high)
	@echo -e "$(BLUE)📋 Creating task...$(NC)"
	./kimi-cli task --title "$(TITLE)" --priority $(PRIORITY)

# List all tasks
tasks: ## List all tasks
	@echo -e "$(BLUE)📋 Listing tasks...$(NC)"
	./kimi-cli list

# Run optimization
optimize: ## Run project optimization
	@echo -e "$(BLUE)💰 Running optimization...$(NC)"
	./kimi-cli optimize

# Perform human checkin
checkin: ## Perform human checkin
	@echo -e "$(BLUE)👋 Human checkin...$(NC)"
	./kimi-cli checkin

# Generate project report
report: ## Generate comprehensive project report
	@echo -e "$(BLUE)📈 Generating project report...$(NC)"
	./kimi-cli report

## Testing

# Run all tests
test: ## Run all tests
	@echo -e "$(BLUE)🧪 Running tests...$(NC)"
	python -m pytest tests/ -v

# Run only Kimi tests
test-kimi: ## Run only Kimi Instruct tests
	@echo -e "$(BLUE)🧪 Running Kimi tests...$(NC)"
	python -m pytest tests/test_kimi_integration.py -v

# Run tests with coverage
test-coverage: ## Run tests with coverage report
	@echo -e "$(BLUE)📊 Running tests with coverage...$(NC)"
	python -m pytest tests/ --cov=src --cov-report=html --cov-report=term

## Monitoring Operations

# Check system health
health: ## Check health of all services
	@echo -e "$(BLUE)❤️  Checking system health...$(NC)"
	@curl -s http://localhost:8084/health | jq . || echo "Kimi not available"
	@curl -s http://localhost:9090/-/healthy && echo -e "$(GREEN)✅ Prometheus healthy$(NC)" || echo -e "$(RED)❌ Prometheus unhealthy$(NC)"
	@curl -s http://localhost:3000/api/health && echo -e "$(GREEN)✅ Grafana healthy$(NC)" || echo -e "$(RED)❌ Grafana unhealthy$(NC)"

# View all logs
logs: ## View logs from all services
	@echo -e "$(BLUE)📄 Viewing all service logs...$(NC)"
	docker-compose logs -f

# Clean up everything
clean: ## Clean up containers, volumes, and networks
	@echo -e "$(YELLOW)🧽 Cleaning up...$(NC)"
	docker-compose down -v --remove-orphans
	docker system prune -f
	@echo -e "$(GREEN)✅ Cleanup complete$(NC)"

# Reset everything (nuclear option)
reset: clean ## Complete reset - removes everything
	@echo -e "$(RED)⚠️  Performing complete reset...$(NC)"
	docker-compose down -v --remove-orphans --rmi all
	docker system prune -a -f --volumes
	rm -rf kimi_workspace/* logs/*
	@echo -e "$(GREEN)✅ Complete reset done$(NC)"

## Development

# Format code
format: ## Format code with black and isort
	@echo -e "$(BLUE)✨ Formatting code...$(NC)"
	black src/ tests/
	isort src/ tests/
	@echo -e "$(GREEN)✅ Code formatted$(NC)"

# Lint code
lint: ## Lint code with mypy
	@echo -e "$(BLUE)🔍 Linting code...$(NC)"
	mypy src/
	@echo -e "$(GREEN)✅ Code linted$(NC)"

# Development setup
dev-setup: install build ## Complete development setup
	@echo -e "$(GREEN)🎉 Development environment ready!$(NC)"

## Information

# Show help
help: ## Show this help message
	@echo -e "$(BLUE)LabVerse Monitoring Stack with Kimi Instruct$(NC)"
	@echo -e "$(BLUE)==============================================$(NC)"
	@echo -e "$(YELLOW)Available targets:$(NC)"
	@awk 'BEGIN {FS = ":.*##"} /^[$$()% a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)
	@echo -e "\n$(BLUE)Examples:$(NC)"
	@echo -e "  make install-kimi     # Install Kimi AI project manager"
	@echo -e "  make up               # Start the complete stack"
	@echo -e "  make status           # Check project status"
	@echo -e "  make optimize         # Run cost optimization"
	@echo -e "  make kimi-dashboard   # Open Kimi dashboard"
	@echo -e "\n$(GREEN)Your AI-powered monitoring stack awaits! 🚀$(NC)"

# Show stack status
info: ## Show detailed stack information
	@echo -e "$(BLUE)LabVerse Monitoring Stack Information$(NC)"
	@echo -e "$(BLUE)=====================================$(NC)"
	@echo -e "$(YELLOW)Services:$(NC)"
	@docker-compose ps
	@echo -e "\n$(YELLOW)Networks:$(NC)"
	@docker network ls | grep monitoring
	@echo -e "\n$(YELLOW)Volumes:$(NC)"
	@docker volume ls | grep -E '(kimi|monitoring)'

.PHONY: install build up down restart install-kimi kimi-up kimi-down kimi-restart kimi-logs kimi-status kimi-dashboard status task tasks optimize checkin report test test-kimi test-coverage health logs clean reset format lint dev-setup help info