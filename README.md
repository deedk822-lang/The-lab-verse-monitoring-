# Clone and setup
git clone <repo>
cd vaal-ai-empire

# Quick start (everything automated)
make quickstart

# Or manual setup
make setup
make docker-up

# Run orchestrator
make run

# Or execute single directive
python rainmaker_orchestrator.py "Analyze project history"