#!/bin/bash
set -e

echo "🤖 Lab-Verse Agent - Model Download Script"
echo "=========================================="

mkdir -p ./models
cd ./models

MODELS=(
  "mistralai/Mistral-7B-Instruct-v0.3"
  "microsoft/phi-2"
  "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
)

echo "📥 Downloading models for local inference..."

for model in "${MODELS[@]}"; do
  echo ""
  echo "Downloading: $model"
  huggingface-cli download "$model" --cache-dir . --resume-download
  echo "✅ Downloaded: $model"
done

echo ""
echo "✅ All models downloaded successfully!"
echo "📍 Location: ./models"
echo "Total size (~15GB):"
du -sh .
