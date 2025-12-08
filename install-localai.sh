#!/bin/bash
set -e

echo "🤖 Installing LocalAI..."

# Create directory
mkdir -p ~/localai
cd ~/localai

# Download LocalAI with Docker
docker pull quay.io/go-skynet/local-ai:latest

# Create models directory
mkdir -p models

echo "✅ LocalAI installed!"
echo "📝 Next: Download models with download-models.sh"
