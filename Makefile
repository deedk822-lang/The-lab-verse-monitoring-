# Makefile - FIXED
.PHONY: test run-orchestrator validate

# ✅ Use absolute path or check file existence
run-orchestrator:
	@if [ -f "rainmaker_orchestrator.py" ]; then \
		python rainmaker_orchestrator.py; \
	elif [ -f "api/rainmaker_orchestrator.py" ]; then \
		python api/rainmaker_orchestrator.py; \
	else \
		echo "❌ Error: rainmaker_orchestrator.py not found"; \
		exit 1; \
	fi

validate:
	@echo "Validating project structure..."
	@python scripts/validate_env.py

test:
	@python -m pytest tests/ -v
