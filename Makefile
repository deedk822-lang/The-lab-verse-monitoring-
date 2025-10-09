# Makefile for The LabVerse Monitoring Stack

# ==============================================================================
# Main Stack Commands
# ==============================================================================

# Start all services in the stack
up:
	docker-compose up -d

# Stop all services
down:
	docker-compose down

# View the status of all services
status:
	docker-compose ps

# View logs for all services
logs:
	docker-compose logs -f

# ==============================================================================
# Kimi Instruct AI Project Manager Commands
# ==============================================================================

# Install Kimi by running the installation script
install-kimi:
	@chmod +x scripts/install-kimi.sh
	@./scripts/install-kimi.sh

# Start the Kimi service
kimi-up:
	docker-compose up -d kimi-project-manager

# Stop the Kimi service
kimi-down:
	docker-compose stop kimi-project-manager

# View the logs for the Kimi service
kimi-logs:
	docker-compose logs -f kimi-project-manager

# Get the status of the Kimi service via its CLI
kimi-status:
	docker-compose exec kimi-project-manager python -m src.kimi_instruct.cli status

# ==============================================================================
# Development and Testing
# ==============================================================================

# Install Python dependencies for Kimi
install-deps:
	pip install -r requirements.kimi.txt

# Run integration tests for Kimi
test:
	PYTHONPATH=. pytest tests/test_kimi_integration.py

.PHONY: up down status logs install-kimi kimi-up kimi-down kimi-logs kimi-status install-deps test