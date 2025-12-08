#!/bin/bash

echo "🛑 Stopping all AI services..."

# Stop Ollama
sudo systemctl stop ollama

# Stop LocalAI
docker stop localai

# Stop Stable Diffusion
pkill -f "webui.sh"

# Stop Qwen-VL
pkill -f "web_demo.py"

echo "✅ All services stopped"
