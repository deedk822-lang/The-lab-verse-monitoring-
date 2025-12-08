#!/bin/bash
set -e

echo "📥 Downloading Ollama models..."

# Mistral
ollama pull mistral:7b-instruct

# Llama 3
ollama pull llama3:8b

# Qwen (Chinese + English)
ollama pull qwen:7b

# CodeLlama
ollama pull codellama:7b

# Phi-3
ollama pull phi3:mini

# Mixtral (more capable, needs more RAM)
ollama pull mixtral:8x7b

# Gemma
ollama pull gemma:2b

echo "✅ All Ollama models ready!"
echo "🚀 Test with: ollama run mistral:7b-instruct"
