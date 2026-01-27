#!/bin/bash
# Setup script for Rainmaker Orchestrator

set -e

echo "Setting up Rainmaker Orchestrator with GLM-4.7 and AutoGLM..."

# Create virtual environment if not exists
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install requirements
pip install -r requirements.txt

# Create logs directory
mkdir -p logs

echo "Setup complete!"
echo "To start the application:"
echo "  source venv/bin/activate"
echo "  uvicorn src.main:app --reload --host 0.0.0.0 --port 8000"
