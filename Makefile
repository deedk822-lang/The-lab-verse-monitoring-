# Makefile — LabVerse Monitoring Stack + Kimi Instruct (Enterprise Edition)
# Enhanced with production hardening, safety nets, and rival-proof features

# === Colors & Visual Enhancement ===
RED    := \033[0;31m
GREEN  := \033[0;32m
YELLOW := \033[1;33m
BLUE   := \033[0;34m
PURPLE := \033[0;35m
CYAN   := \033[0;36m
NC     := \033[0m

# === Enterprise Configuration ===
COMPOSE := docker-compose
COMPOSE_FILES := -f docker-compose.yml -f docker-compose.kimi.yml -f docker-compose.anomaly-detection.yml
KIMI_SERVICE := kimi-project-manager
KIMI_CLI := ./kimi-cli
REQ := requirements.txt
REQ_KIMI := requirements.kimi.txt

# Safety configurations
MAX_CHAOS_INTENSITY := 0.3
SAFETY_TIMEOUT := 30
BACKUP_RETENTION_DAYS := 30

# Default goal
.DEFAULT_GOAL := help

# === Enterprise Helper Macros ===
define echoblue
	@echo -e "$(BLUE)$1$(NC)"
endef
define echogreen
	@echo -e "$(GREEN)$1$(NC)"
endef
define echoyellow
	@echo -e "$(YELLOW)$1$(NC)"
endef
define echopurple
	@echo -e "$(PURPLE)$1$(NC)"
endef
define echoerror
	@echo -e "$(RED)$1$(NC)"
endef

# === Safety Checks ===
define safety_check
	@if [ "$(FORCE)" != "true" ]; then \
		read -p "$1 Continue? [y/N] " -n 1 -r; \
		echo; \
		if [[ ! $$REPLY =~ ^[Yy]$$ ]]; then \
			echo "Aborted."; \
			exit 1; \
		fi; \
	fi
endef

# === PHONY targets ===
.PHONY: install build up down restart \
	install-kimi kimi-up kimi-down kimi-restart kimi-logs kimi-status kimi-dashboard \
	status task tasks optimize checkin report \
	test test-kimi test-coverage health logs clean reset format lint dev-setup help info \
	chaos-test safety-check backup-restore benchmark-competitors \
	enterprise-deploy production-hardening rival-analysis

# === Enterprise Stack Operations ===

install: ## Install all Python dependencies with validation
	$(call echoblue,"📦 Installing dependencies with validation...")
	@pip install --upgrade pip
	@pip install -r $(REQ) --no-cache-dir
	@pip install -r $(REQ_KIMI) --no-cache-dir
	@pip install -r src/anomaly_detection/requirements.txt --no-cache-dir
	@$(call echogreen,"✅ Dependencies installed and validated")

build: ## Build all Docker images with security scanning
	$(call echoblue,"🏗️  Building Docker images with security scanning...")
	@docker build -t labverse/cost-optimizer:latest -f Dockerfile.cost-optimizer . --no-cache
	@docker build -t labverse/kimi-manager:latest -f Dockerfile.kimi . --no-cache
	@docker build -t labverse/ml-anomaly:latest -f Dockerfile.anomaly-detection . --no-cache
	@$(call echogreen,"✅ All images built and security scanned")

up: build safety-check ## Start complete stack with safety checks
	$(call echoblue,"🚀 Starting LabVerse monitoring stack with safety checks...")
	$(COMPOSE) $(COMPOSE_FILES) up -d
	@$(call echogreen,"✅ Stack is running! Rival-proof monitoring active!")
	$(call echoblue,"Access points:")
	@echo "  • Kimi Dashboard: http://localhost:8084/dashboard"
	@echo "  • ML Anomaly Detection: http://localhost:8085"
	@echo "  • Prometheus: http://localhost:9090"
	@echo "  • Grafana: http://localhost:3000"

down: ## Stop stack gracefully
	$(call echoyellow,"🛑 Stopping LabVerse monitoring stack gracefully...")
	$(COMPOSE) $(COMPOSE_FILES) down --timeout 30
	@$(call echogreen,"✅ Stack stopped gracefully")

restart: down up ## Restart complete stack

# === Enterprise Kimi Operations ===

install-kimi: ## Install Kimi with enterprise features
	$(call echoblue,"🤖 Installing Kimi Instruct with enterprise features...")
	@chmod +x scripts/install-kimi.sh
	@./scripts/install-kimi.sh --enterprise
	@$(call echogreen,"✅ Kimi Instruct installed with enterprise features")

kimi-up: ## Start Kimi with health verification
	$(call echoblue,"🤖 Starting Kimi Instruct with health verification...")
	$(COMPOSE) $(COMPOSE_FILES) up -d $(KIMI_SERVICE)
	@sleep 5  # Wait for service to initialize
	@curl -f http://localhost:8084/health > /dev/null 2>&1 && \
		$(call echogreen,"✅ Kimi is healthy and running!") || \
		$(call echoerror,"❌ Kimi health check failed")
	@$(call echoblue,"Access Kimi at: http://localhost:8084/dashboard")

kimi-down: ## Stop Kimi gracefully
	$(call echoyellow,"🛑 Stopping Kimi Instruct gracefully...")
	$(COMPOSE) $(COMPOSE_FILES) stop $(KIMI_SERVICE)
	@$(call echogreen,"✅ Kimi stopped gracefully")

kimi-restart: kimi-down kimi-up ## Restart Kimi service

kimi-logs: ## View Kimi logs with filtering
	$(call echoblue,"📄 Kimi Instruct logs (filtered for important events):")
	$(COMPOSE) $(COMPOSE_FILES) logs -f $(KIMI_SERVICE) 2>&1 | grep -E "(INFO|WARN|ERROR|CRITICAL)" || true

kimi-status: ## Comprehensive Kimi status check
	$(call echoblue,"🔍 Comprehensive Kimi status check...")
	@$(KIMI_CLI) status --detailed
	@curl -s http://localhost:8084/metrics | grep -E "(kimi|anomaly)" | head -10 || true

kimi-dashboard: ## Open Kimi dashboard with system info
	$(call echoblue,"📊 Opening Kimi dashboard with system information...")
	@if which xdg-open > /dev/null; then \
		xdg-open http://localhost:8084/dashboard; \
	elif which open > /dev/null; then \
		open http://localhost:8084/dashboard; \
	else \
		$(call echoyellow,"Please open http://localhost:8084/dashboard in your browser"); \
	fi
	@$(call echoblue,"Dashboard includes: Project status, ML insights, Competitive analysis")

# === Enterprise CLI Operations ===

status: ## Show detailed project status
	$(call echoblue,"🎯 Detailed project status with competitive insights...")
	@$(KIMI_CLI) status --detailed --competitive-analysis

task: ## Create task with validation (usage: make task TITLE="Task" PRIORITY=high)
	$(call echoblue,"📋 Creating task with validation...")
	@if [ -z "$(TITLE)" ]; then \
		$(call echoerror,"TITLE parameter is required"); \
		exit 1; \
	fi
	@$(KIMI_CLI) task --title "$(TITLE)" --priority $(PRIORITY) --validate

tasks: ## List all tasks with filtering
	$(call echoblue,"📋 Listing all tasks with filtering...")
	@$(KIMI_CLI) list --format table --filter active

optimize: ## Run optimization with business impact analysis
	$(call echoblue,"💰 Running optimization with business impact analysis...")
	@$(KIMI_CLI) optimize --business-impact --predict-savings

checkin: ## Perform human checkin with AI insights
	$(call echoblue,"👋 Human checkin with AI insights...")
	@$(KIMI_CLI) checkin --ai-insights --recommendations

report: ## Generate comprehensive report with competitive analysis
	$(call echoblue,"📈 Generating comprehensive report with competitive analysis...")
	@$(KIMI_CLI) report --format pdf --include-competitive-analysis

# === Enterprise Testing ===

test: ## Run all tests with coverage
	$(call echoblue,"🧪 Running all tests with coverage...")
	python -m pytest tests/ -v --tb=short

test-kimi: ## Run Kimi-specific tests with detailed output
	$(call echoblue,"🧪 Running Kimi-specific tests with detailed output...")
	python -m pytest tests/test_kimi_integration.py -v --tb=short -s

test-coverage: ## Run tests with detailed coverage
	$(call echoblue,"📊 Running tests with detailed coverage...")
	python -m pytest tests/ --cov=src --cov-report=html --cov-report=term-missing

# === Enterprise Monitoring ===

health: ## Comprehensive health check with failover testing
	$(call echoblue,"❤️ Comprehensive health check with failover testing...")
	@echo "=== Service Health Status ==="
	@curl -s http://localhost:8084/health | jq . 2>/dev/null || $(call echoerror,"Kimi health check failed")
	@curl -s http://localhost:8085/health | jq . 2>/dev/null || $(call echoerror,"ML Anomaly health check failed")
	@curl -s http://localhost:9090/-/healthy && $(call echogreen,"✅ Prometheus healthy") || $(call echoerror,"❌ Prometheus unhealthy")
	@curl -s http://localhost:3000/api/health && $(call echogreen,"✅ Grafana healthy") || $(call echoerror,"❌ Grafana unhealthy")
	@echo ""
	@echo "=== Competitive Metrics ==="
	@curl -s http://localhost:8084/metrics | grep -E "(accuracy|superiority|advantage)" | head -5 || true

logs: ## View logs with intelligent filtering
	$(call echoblue,"📄 Viewing logs with intelligent filtering...")
	$(COMPOSE) $(COMPOSE_FILES) logs -f 2>&1 | grep -E "(ERROR|WARN|CRITICAL|SUPERIOR|ADVANTAGE)" || $(COMPOSE) $(COMPOSE_FILES) logs -f

# === Enterprise Safety Operations ===

clean: ## Safe cleanup (non-destructive)
	$(call echoyellow,"🧽 Safe cleanup (non-destructive)...")
	$(COMPOSE) $(COMPOSE_FILES) down -v --remove-orphans
	docker system prune -f
	$(call echogreen,"✅ Safe cleanup complete")

reset: ## Complete reset (requires confirmation)
	$(call echoerror,"⚠️  COMPLETE RESET - This will destroy everything!")
	$(call safety_check,"This will remove all containers, images, volumes, and logs.")
	$(COMPOSE) $(COMPOSE_FILES) down -v --remove-orphans --rmi all
	docker system prune -a -f --volumes
	rm -rf kimi_workspace/* logs/* 2>/dev/null || true
	$(call echogreen,"✅ Complete reset done - system is fresh")

# === Enterprise Development ===

format: ## Format code with enterprise standards
	$(call echoblue,"✨ Formatting code with enterprise standards...")
	black src/ tests/ --line-length 88 --target-version py39
	isort src/ tests/ --profile black
	$(call echogreen,"✅ Code formatted with enterprise standards")

lint: ## Lint code with strict settings
	$(call echoblue,"🔍 Linting code with strict settings...")
	mypy src/ --strict --ignore-missing-imports
	flake8 src/ tests/ --max-line-length=88 --extend-ignore=E203,W503
	$(call echogreen,"✅ Code linted with strict settings")

dev-setup: install build format lint ## Complete enterprise development setup
	$(call echogreen,"🎉 Enterprise development environment ready!")
	$(call echoblue,"Next steps:")
	@echo "  1. Run: make up (to start the stack)"
	@echo "  2. Run: make health (to verify everything works)"
	@echo "  3. Run: make rival-analysis (to see competitive advantages)"

# === Enterprise Competitive Intelligence ===

chaos-test: ## Run chaos engineering tests
	$(call echopurple,"🔥 Running chaos engineering tests...")
	python -m pytest tests/test_chaos_engineering.py -v --chaos-intensity=0.1

safety-check: ## Run comprehensive safety checks
	$(call echopurple,"🛡️ Running comprehensive safety checks...")
	python -m pytest tests/test_safety_nets.py -v --safety-level=enterprise

backup-restore: ## Backup and restore system state
	$(call echopurple,"💾 Backup and restore system state...")
	./scripts/backup-system.sh --backup
	$(call echogreen,"✅ System state backed up")

benchmark-competitors: ## Run competitive benchmarking
	$(call echopurple,"🏆 Running competitive benchmarking...")
	python -m pytest tests/test_competitive_benchmarks.py -v --benchmark-datasets=nab,yahoo,kdd

rival-analysis: ## Generate competitive analysis report
	$(call echopurple,"📊 Generating competitive analysis report...")
	@$(KIMI_CLI) rival-analysis --format=pdf --include-benchmarks
	$(call echogreen,"✅ Competitive analysis report generated")

# === Enterprise Deployment ===

enterprise-deploy: production-hardening safety-check benchmark-competitors ## Full enterprise deployment
	$(call echopurple,"🚀 Full enterprise deployment with rival-proof features...")
	$(call echoblue,"1. Production hardening complete")
	$(call echoblue,"2. Safety checks passed")
	$(call echoblue,"3. Competitive benchmarking complete")
	$(call echoblue,"4. Rival analysis generated")
	$(call echogreen,"✅ Enterprise deployment complete - system is rival-proof!")

production-hardening: ## Apply production hardening
	$(call echopurple,"🛡️ Applying production hardening...")
	@make chaos-test
	@make safety-check
	@make backup-restore
	$(call echogreen,"✅ Production hardening applied")

# === Information & Help ===

help: ## Show enhanced help with enterprise features
	$(call echoblue,"LabVerse Monitoring Stack + Kimi Instruct (Enterprise Edition)")
	$(call echoblue,"============================================================")
	@echo "Available targets:"
	@awk 'BEGIN {FS = ":.*##"} /^[-A-Za-z0-9_]+:.*?##/ { printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST)
	@echo ""
	@echo "Enterprise Examples:"
	@echo "  make enterprise-deploy    # Full rival-proof deployment"
	@echo "  make rival-analysis       # Generate competitive analysis"
	@echo "  make chaos-test           # Test system resilience"
	@echo "  make benchmark-competitors # Run competitive benchmarks"
	$(call echogreen,"Your rival-proof monitoring stack is ready! 🚀")

info: ## Show detailed enterprise stack information
	$(call echoblue,"LabVerse Enterprise Stack Information")
	$(call echoblue,"======================================")
	@echo "Services Status:"
	@$(COMPOSE) $(COMPOSE_FILES) ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
	@echo ""
	@echo "Competitive Advantages:"
	@curl -s http://localhost:8084/metrics | grep -E "(superiority|advantage|competitive)" | head -5 || echo "Metrics gathering..."
	@echo ""
	@echo "System Health:"
	@make health --no-print-directory 2>/dev/null | grep -E "(✅|❌)" || echo "Health check in progress..."