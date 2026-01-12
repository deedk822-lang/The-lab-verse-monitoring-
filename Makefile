.PHONY: quickstart setup docker-up run

quickstart: setup docker-up run

setup:
	@echo "Setting up environment..."
	pip install -r requirements.txt

docker-up:
	@echo "Starting services with Docker Compose..."
	docker-compose up -d

run:
	@echo "Running Rainmaker Orchestrator..."
	python rainmaker-orchestrator/orchestrator.py
