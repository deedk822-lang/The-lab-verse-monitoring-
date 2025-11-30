#!/usr/bin/env bash

set -e

echo "🚀 Installing LocalAI with Mistral..."

# Detect OS
OS="$(uname)"
if [[ "${OS}" == "Linux" ]]; then
  CLI_ON_LINUX=1
elif [[ "${OS}" == "Darwin" ]]; then
  CLI_ON_MACOS=1
else
  echo "❌ Only Linux and macOS supported"
  exit 1
fi

# Create directories
mkdir -p models localai-data

# Download LocalAI binary
echo "📥 Downloading LocalAI..."
if [[ -n "${CLI_ON_MACOS-}" ]]; then
  curl -Lo ./localai https://github.com/mudler/LocalAI/releases/download/v2.16.0/local-ai-Darwin-arm64
elif [[ -n "${CLI_ON_LINUX-}" ]]; then
  curl -Lo ./localai https://github.com/mudler/LocalAI/releases/download/v2.16.0/local-ai-Linux-x86_64
fi

chmod +x ./localai

# Download Mistral model
echo "📥 Downloading Mistral model config..."
curl -Lo models/mistral-7b-instruct.yaml https://raw.githubusercontent.com/mudler/LocalAI/master/embedded/models/mistral-7b-instruct.yaml

# Start LocalAI
echo "🚀 Starting LocalAI on port 8080..."
./localai --models-path ./models --address :8080 &

echo "✅ LocalAI installed and running!"
echo "Test: curl http://localhost:8080/v1/models"
