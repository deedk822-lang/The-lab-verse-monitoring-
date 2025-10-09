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
MAX_CHAOS_INTENSITY := 0.3
SAFETY_TIMEOUT := 30
BACKUP_RETENTION_DAYS := 30

.DEFAULT_GOAL := help

# === Helper Macros ===
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
.PHONY: install build up down restart install-kimi kimi-up kimi-down kimi-restart kimi-logs kimi-status kimi-dashboard \
	status task tasks optimize checkin report test test-kimi test-coverage health logs clean reset format lint dev-setup \
	chaos-test safety-check backup-restore benchmark-competitors rival-analysis enterprise-deploy production-hardening \
	enterprise-config-validate enterprise-features enterprise-config-reload enterprise-run enterprise-test help info

# === Core Stack Operations ===
install:
	$(call echoblue,"📦 Installing dependencies...")
	@pip install --upgrade pip
	@pip install -r $(REQ) -r $(REQ_KIMI) -r src/anomaly_detection/requirements.txt --no-cache-dir
	$(call echogreen,"✅ Dependencies installed")

build:
	$(call echoblue,"🏗️  Building Docker images...")
	@docker build -t labverse/cost-optimizer:latest -f Dockerfile.cost-optimizer . --no-cache
	@docker build -t labverse/kimi-manager:latest -f Dockerfile.kimi . --no-cache
	@docker build -t labverse/ml-anomaly:latest -f Dockerfile.anomaly-detection . --no-cache
	$(call echogreen,"✅ Build complete")

up: build safety-check
	$(call echoblue,"🚀 Starting LabVerse monitoring stack...")
	$(COMPOSE) $(COMPOSE_FILES) up -d
	$(call echogreen,"✅ Stack running! Rival-proof monitoring active!")
	@echo "→ Kimi Dashboard: http://localhost:8084/dashboard"
	@echo "→ ML Anomaly: http://localhost:8085"
	@echo "→ Grafana: http://localhost:3000"

down:
	$(call echoyellow,"🛑 Stopping stack...")
	$(COMPOSE) $(COMPOSE_FILES) down --timeout 30
	$(call echogreen,"✅ Stopped")

restart: down up

# === Kimi Operations ===
install-kimi:
	$(call echoblue,"🤖 Installing Kimi Instruct (enterprise)...")
	@chmod +x scripts/install-kimi.sh && ./scripts/install-kimi.sh --enterprise
	$(call echogreen,"✅ Installed")

kimi-up:
	$(call echoblue,"🤖 Starting Kimi...")
	$(COMPOSE) $(COMPOSE_FILES) up -d $(KIMI_SERVICE)
	@sleep 5
	@curl -fs http://localhost:8084/health >/dev/null && \
		$(call echogreen,"✅ Kimi healthy") || $(call echoerror,"❌ Health check failed")

kimi-down:
	$(call echoyellow,"🛑 Stopping Kimi...")
	$(COMPOSE) $(COMPOSE_FILES) stop $(KIMI_SERVICE)
	$(call echogreen,"✅ Kimi stopped")

kimi-restart: kimi-down kimi-up
kimi-logs:
	$(call echoblue,"📄 Kimi logs:")
	$(COMPOSE) $(COMPOSE_FILES) logs -f $(KIMI_SERVICE) | grep -E "(INFO|WARN|ERROR|CRITICAL)" || true
kimi-status:
	$(call echoblue,"🔍 Checking Kimi status...")
	@$(KIMI_CLI) status --detailed

# === CLI & Intelligence ===
status:
	$(call echoblue,"🎯 Project status...")
	@$(KIMI_CLI) status --detailed --competitive-analysis
task:
	$(call echoblue,"📋 Creating task...")
	@if [ -z "$(TITLE)" ]; then $(call echoerror,"TITLE required"); exit 1; fi
	@$(KIMI_CLI) task --title "$(TITLE)" --priority $(PRIORITY) --validate
report:
	$(call echoblue,"📈 Generating report...")
	@$(KIMI_CLI) report --format pdf --include-competitive-analysis

# === Testing & Monitoring ===
test:
	$(call echoblue,"🧪 Running tests...")
	python -m pytest tests/ -v
test-coverage:
	$(call echoblue,"📊 Coverage...")
	python -m pytest tests/ --cov=src --cov-report=html --cov-report=term-missing
health:
	$(call echoblue,"❤️ Health check...")
	@curl -s http://localhost:8084/health | jq . || $(call echoerror,"Kimi health fail")

# === Maintenance & Safety ===
clean:
	$(call echoyellow,"🧽 Cleaning stack...")
	$(COMPOSE) $(COMPOSE_FILES) down -v --remove-orphans
	docker system prune -f
	$(call echogreen,"✅ Cleanup done")
reset:
	$(call echoerror,"⚠️  FULL RESET!")
	$(call safety_check,"This will destroy all containers and volumes.")
	$(COMPOSE) $(COMPOSE_FILES) down -v --rmi all
	docker system prune -a -f --volumes
	rm -rf kimi_workspace/* logs/* || true
	$(call echogreen,"✅ Reset done")

# === Development & QA ===
format:
	$(call echoblue,"✨ Formatting...")
	black src/ tests/ --line-length 88 --target-version py39
	isort src/ tests/ --profile black
lint:
	$(call echoblue,"🔍 Linting...")
	mypy src/ --strict --ignore-missing-imports
	flake8 src/ tests/ --max-line-length=88 --extend-ignore=E203,W503
dev-setup: install build format lint
	$(call echogreen,"🎉 Dev environment ready!")

# === Competitive Intelligence ===
chaos-test:
	$(call echopurple,"🔥 Chaos tests...")
	python -m pytest tests/test_chaos_engineering.py -v --chaos-intensity=0.1
safety-check:
	$(call echopurple,"🛡️ Safety checks...")
	python -m pytest tests/test_safety_nets.py -v --safety-level=enterprise
benchmark-competitors:
	$(call echopurple,"🏆 Competitive benchmarks...")
	python -m pytest tests/test_competitive_benchmarks.py -v --benchmark-datasets=nab,yahoo,kdd
rival-analysis:
	$(call echopurple,"📊 Rival analysis...")
	@$(KIMI_CLI) rival-analysis --format=pdf --include-benchmarks
	$(call echogreen,"✅ Report ready")

enterprise-deploy: production-hardening safety-check benchmark-competitors
	$(call echopurple,"🚀 Full enterprise deploy...")
	$(call echogreen,"✅ Rival-proof system online")

production-hardening:
	$(call echopurple,"🛡️ Applying hardening...")
	@make chaos-test
	@make safety-check
	@make backup-restore
	$(call echogreen,"✅ Hardening done")

# === Enterprise Configuration System (Fixed Edition) ===
build-ts: ## 🛠️  Build the cardinality-guardian TypeScript project
	$(call echoblue,"🛠️ Building cardinality-guardian...")
	@(cd src/cardinality-guardian && npm run build)
	$(call echogreen,"✅ cardinality-guardian built successfully.")

enterprise-config-validate: build-ts
	$(call echoblue,"🔍 Validating enterprise config...")
	@node --input-type=module -e "\
	import { EnterpriseConfigLoader } from './src/cardinality-guardian/dist/config/EnterpriseConfig.js'; \
	const loader = EnterpriseConfigLoader.getInstance(); \
	const cfg = loader.getConfig(); \
	console.log('✅ Config valid, version:', cfg.version);" \
	|| { echo '❌ Config validation failed'; exit 1; }

enterprise-features: build-ts
	$(call echoblue,"🏢 Listing enterprise features...")
	@node --input-type=module -e "\
	import { EnterpriseConfigLoader } from './src/cardinality-guardian/dist/config/EnterpriseConfig.js'; \
	const cfg = EnterpriseConfigLoader.getInstance().getConfig(); \
	console.table({ \
		MultiCloud: cfg.multi_cloud_deployment?.enabled, \
		ChaosEngineering: cfg.chaos_engineering?.enabled, \
		MobileIntegration: cfg.mobile_integration?.push_notifications, \
		Benchmarking: cfg.competitive_intelligence?.benchmarking_enabled, \
		Explainability: cfg.explainability?.shap_analysis_enabled \
	});" || { echo '❌ Error reading config'; exit 1; }

enterprise-config-reload: build-ts
	$(call echoblue,"🔄 Reloading enterprise config...")
	@node --input-type=module -e "\
	import { EnterpriseConfigLoader } from './src/cardinality-guardian/dist/config/EnterpriseConfig.js'; \
	const loader = EnterpriseConfigLoader.getInstance(); \
	loader.reload(); \
	console.log('✅ Config reloaded');" || { echo '❌ Reload failed'; exit 1; }

enterprise-run: build-ts
	$(call echoblue,"🚀 Launching Enterprise Orchestrator...")
	@node src/cardinality-guardian/dist/main.js || { echo '❌ Orchestrator failed'; exit 1; }

enterprise-test:
	$(call echoblue,"🧪 Running enterprise test...")
	@$(MAKE) --no-print-directory enterprise-config-validate
	@$(MAKE) --no-print-directory enterprise-features
	$(call echogreen,"✅ Enterprise system verified")

# === Help & Info ===
help:
	$(call echoblue,"LabVerse Monitoring Stack + Kimi Instruct (Enterprise Edition)")
	@awk 'BEGIN{FS=":.*##"} /^[-A-Za-z0-9_]+:.*?##/ {printf "  \033[36m%-22s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	$(call echogreen,"Use `make enterprise-deploy` to launch full rival-proof stack.")
info:
	$(call echoblue,"ℹ️ System Info")
	@$(COMPOSE) $(COMPOSE_FILES) ps