#!/bin/bash

echo "🧪 Testing AI Models..."

# Test Ollama
echo "Testing Ollama Mistral..."
ollama run mistral:7b-instruct "Say hello in 5 words"

# Test LocalAI
echo ""
echo "Testing LocalAI..."
curl -X POST http://localhost:8080/v1/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "mistral", "prompt": "Hello", "max_tokens": 10}'

# Test Stable Diffusion
echo ""
echo "Testing Stable Diffusion..."
curl -X POST http://localhost:7861/sdapi/v1/txt2img \
  -H "Content-Type: application/json" \
  -d '{"prompt": "a cat", "steps": 5, "width": 256, "height": 256}'

echo ""
echo "✅ All tests complete!"
