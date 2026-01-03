.PHONY: generate dev test test-unit test-e2e test-performance security deploy

# Configuration
BACKEND_DIR = generated_project/backend
FRONTEND_DIR = generated_project/frontend
CONTRACT_FILE = contract.yml

# Generate full-stack application from contract
generate:
	@echo "🚀 Generating full-stack application..."
	@python3 professional_ai_system.py --contract $(CONTRACT_FILE) --output generated_project
	@echo "✅ Generation complete! Files created in generated_project/"

# Start development servers
dev: dev-backend dev-frontend

dev-backend:
	@echo "🏃 Starting backend development server..."
	@cd $(BACKEND_DIR) && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &

dev-frontend:
	@echo "🏃 Starting frontend development server..."
	@cd $(FRONTEND_DIR) && npm run dev &

# Run tests
test: test-unit test-e2e test-security

test-unit:
	@echo "🧪 Running unit tests..."
	@cd $(BACKEND_DIR) && pytest -v
	@cd $(FRONTEND_DIR) && npm test

test-e2e:
	@echo "🔍 Running E2E tests..."
	@cd $(FRONTEND_DIR) && npx playwright test

test-performance:
	@echo "📈 Running performance tests..."
	@k6 run tests/performance/load-test.js

test-security:
	@echo "🔒 Running security tests..."
	@cd $(BACKEND_DIR) && bandit -r . -f json -o security-report.json
	@echo "Security report saved to $(BACKEND_DIR)/security-report.json"

security:
	@echo "🛡️ Running comprehensive security scan..."
	@cd $(BACKEND_DIR) && bandit -r . -lll
	@cd $(BACKEND_DIR) && ruff check .
	@cd $(FRONTEND_DIR) && npx eslint .

# Deploy (placeholder - customize for your deployment target)
deploy:
	@echo "☁️ Deploying application..."
	@echo "Note: Configure your deployment pipeline (Vercel/Render/Docker) here"
	@echo "For now, build manually:"
	@echo "  cd $(BACKEND_DIR) && docker build -t backend ."
	@echo "  cd $(FRONTEND_DIR) && npm run build"

# Clean generated files
clean:
	@echo "🧹 Cleaning generated files..."
	@rm -rf generated_project/*
	@rm -rf generated_types/*

# Show project status
status:
	@echo "📊 Project Status:"
	@echo "Backend: $(BACKEND_DIR)"
	@echo "Frontend: $(FRONTEND_DIR)"
	@echo "Contract: $(CONTRACT_FILE)"
	@echo "Files: $$(find generated_project -type f | wc -l) total"

# Help
help:
	@echo "🎯 Professional Full-Stack Generator"
	@echo ""
	@echo "Usage:"
	@echo "  make generate          # Generate full-stack application"
	@echo "  make dev              # Start development servers"
	@echo "  make test             # Run all tests"
	@echo "  make test-unit        # Run unit tests only"
	@echo "  make test-e2e         # Run E2E tests only"
	@echo "  make test-performance # Run performance tests"
	@echo "  make security         # Run security scans"
	@echo "  make deploy           # Deploy application"
	@echo "  make clean            # Clean generated files"
	@echo "  make status           # Show project status"
	@echo "  make help             # Show this help"
	@echo ""
	@echo "Environment:"
	@echo "  Set MOONSHOT_API_KEY for AI generation"
	@echo "  Configure deployment in Makefile"
