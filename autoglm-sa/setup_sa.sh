#!/bin/bash
# South Africa optimized AutoGLM setup

echo "🇿🇦 Setting up AutoGLM for South Africa..."

# Check for local model first
if [ -f "models/autoglm-phone-9b-multilingual" ]; then
    echo "✅ Using local model (no internet needed)"
    MODEL_URL="http://localhost:8000/v1"
    MODEL_NAME="autoglm-phone-9b-multilingual"
    API_KEY=""
else
    echo "🌐 Using cloud model (internet required)"
    MODEL_URL="https://api.z.ai/api/paas/v4"
    MODEL_NAME="autoglm-phone-multilingual"
    API_KEY="your-api-key"
fi

# Start AutoGLM with SA optimizations
python3 main.py \
  --base-url "$MODEL_URL" \
  --model "$MODEL_NAME" \
  --apikey "$API_KEY" \
  --max-steps 50 \
  --timeout 30 \
  --cache-enabled \
  --retry-attempts 2
