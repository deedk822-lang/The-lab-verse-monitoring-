#!/bin/bash
set -e

echo "🦙 Installing Ollama..."

# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Start Ollama service
sudo systemctl start ollama
sudo systemctl enable ollama

echo "✅ Ollama installed!"
