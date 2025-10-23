# AI Content Creation Suite Makefile

.PHONY: help install start dev test build clean docker-build docker-run docker-stop setup

# Default target
help:
	@echo "AI Content Creation Suite - Available Commands:"
	@echo ""
	@echo "  install     - Install dependencies"
	@echo "  setup       - Run initial setup"
	@echo "  start       - Start production server"
	@echo "  dev         - Start development server with nodemon"
	@echo "  test        - Run test suite"
	@echo "  build       - Build for production"
	@echo "  clean       - Clean build artifacts"
	@echo ""
	@echo "Docker Commands:"
	@echo "  docker-build - Build Docker image"
	@echo "  docker-run   - Run Docker container"
	@echo "  docker-stop  - Stop Docker container"
	@echo "  docker-up    - Start all services with docker-compose"
	@echo "  docker-down  - Stop all services"
	@echo ""
	@echo "Development:"
	@echo "  install-localai - Install LocalAI"
	@echo "  health-check    - Run health check"

# Install dependencies
install:
	npm install

# Run setup script
setup:
	node scripts/setup.js

# Start production server
start:
	npm start

# Start development server
dev:
	npm run dev

# Run tests
test:
	npm test

# Build for production
build:
	npm run build

# Clean build artifacts
clean:
	rm -rf node_modules
	rm -rf logs
	rm -rf uploads
	rm -rf .env

# Docker commands
docker-build:
	docker build -t ai-content-suite .

docker-run:
	docker run -p 3000:3000 --env-file .env ai-content-suite

docker-stop:
	docker stop $$(docker ps -q --filter ancestor=ai-content-suite)

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

# Install LocalAI
install-localai:
	chmod +x scripts/install-localai.sh
	./scripts/install-localai.sh

# Health check
health-check:
	node healthcheck.js

# Development helpers
logs:
	docker-compose logs -f

restart:
	docker-compose restart

# Full setup for new environment
full-setup: install setup
	@echo "Full setup completed!"
	@echo "Next steps:"
	@echo "1. Configure your API keys in .env file"
	@echo "2. Run 'make start' to start the server"
	@echo "3. Open http://localhost:3000 in your browser"