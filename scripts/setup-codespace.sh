#!/bin/bash
# Setup script for GitHub Codespace

set -e

echo "🚀 Setting up PR Fix Agent in Codespace..."

# Install Python dependencies
pip install -e ".[dev]" 2>/dev/null || pip install ollama pytest

# Setup Ollama
if ! command -v ollama &> /dev/null; then
    echo "📥 Installing Ollama..."
    curl -fsSL https://ollama.com/install.sh | sh
fi

# Start Ollama
echo "🦙 Starting Ollama..."
# Kill existing ollama if any
killall ollama 2>/dev/null || true
nohup ollama serve > /tmp/ollama.log 2>&1 &

# Wait for startup
echo "⏳ Waiting for Ollama to start..."
sleep 5

# Pull models (async)
echo "📦 Pulling models (deepseek-r1:1.5b)..."
ollama pull deepseek-r1:1.5b &
OLLAMA_PID=$!

# Setup directories
mkdir -p analysis-results
mkdir -p src/pr_fix_agent

# Wait for models
wait $OLLAMA_PID

echo "✅ Setup complete! Test with:"
echo "   python src/pr_fix_agent/orchestrator.py review --findings analysis-results/test.json"
