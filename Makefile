# Makefile for the Cost Optimizer Service

# Install Python dependencies
install:
	pip install -r requirements.txt

# Run tests (a placeholder for now)
test:
	@echo "Running tests..."
	# Replace this with your actual test command, e.g., pytest
	python -m unittest discover -s tests

# Build the Docker image for the cost optimizer
build:
	docker build -t labverse/cost-optimizer:latest -f Dockerfile.cost-optimizer .

# Run the cost optimizer service using Docker Compose
run:
	docker-compose -f docker-compose.cost-optimizer.yml up

# Stop the service
stop:
	docker-compose -f docker-compose.cost-optimizer.yml down

.PHONY: install test build run stop