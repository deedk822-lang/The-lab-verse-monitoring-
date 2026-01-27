#!/bin/bash
# Automated setup script for Lab-Verse Agent with multi-provider LLM support
# Supports: Z.AI, Qwen/Dashscope, and Hugging Face

set -e

echo "🪐 Lab-Verse Agent - Multi-Provider Setup"
echo "=========================================="
echo ""
echo "Choose your LLM provider:"
echo "  1) Z.AI (requires Z.AI API key)"
echo "  2) Qwen/Dashscope (requires Qwen API key)"
echo "  3) Hugging Face (requires HF token + model download)"
echo ""
read -p "Select option (1-3): " provider_choice

case $provider_choice in
  1)
    PROVIDER="z_ai"
    echo "✅ Using Z.AI provider"
    ;;
  2)
    PROVIDER="qwen"
    echo "✅ Using Qwen/Dashscope provider"
    ;;
  3)
    PROVIDER="huggingface"
    echo "✅ Using Hugging Face local models"
    ;;
  *)
    echo "❌ Invalid choice"
    exit 1
    ;;
esac

echo ""
echo "📂 Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

echo "💾 Installing dependencies..."
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

echo ""
echo "📂 Configuring .env.production..."

cat > .env.production << EOF
LLM_PROVIDER=$PROVIDER
PIPELINE_PLATFORM=bitbucket
ENVIRONMENT=production
LOG_LEVEL=INFO

# Bitbucket Configuration
BITBUCKET_WORKSPACE=lab-verse-monitoring
EOF

# Provider-specific configuration
if [ "$PROVIDER" = "z_ai" ]; then
  echo ""
  echo "🔐 Z.AI API Configuration"
  read -p "Enter your Z.AI API key: " -s z_ai_key
  echo ""
  read -p "Enter Z.AI model for diagnostics [claude-3-5-sonnet-20241022]: " z_ai_diag
  z_ai_diag=${z_ai_diag:-claude-3-5-sonnet-20241022}

  cat >> .env.production << EOF
Z_AI_API_KEY=$z_ai_key
Z_AI_MODEL_DIAGNOSTIC=$z_ai_diag
Z_AI_MODEL_PLANNER=$z_ai_diag
Z_AI_MODEL_EXECUTOR=$z_ai_diag
Z_AI_MODEL_VALIDATOR=$z_ai_diag
EOF

  echo "✅ Z.AI configuration saved (no model download needed)"

elif [ "$PROVIDER" = "qwen" ]; then
  echo ""
  echo "🔐 Qwen/Dashscope API Configuration"
  read -p "Enter your Qwen API key: " -s qwen_key
  echo ""
  read -p "Enter Qwen model for diagnostics [qwen-max]: " qwen_diag
  qwen_diag=${qwen_diag:-qwen-max}

  cat >> .env.production << EOF
QWEN_API_KEY=$qwen_key
QWEN_MODEL_DIAGNOSTIC=$qwen_diag
QWEN_MODEL_PLANNER=$qwen_diag
QWEN_MODEL_EXECUTOR=$qwen_diag
QWEN_MODEL_VALIDATOR=$qwen_diag
EOF

  echo "✅ Qwen configuration saved (no model download needed)"

elif [ "$PROVIDER" = "huggingface" ]; then
  echo ""
  echo "🔐 Hugging Face Configuration"
  read -p "Enter your HF token: " -s hf_token
  echo ""
  read -p "Enter HF device [cuda]: " hf_device
  hf_device=${hf_device:-cuda}

  cat >> .env.production << EOF
HF_TOKEN=$hf_token
HF_DEVICE=$hf_device
HF_LOAD_IN_8BIT=true
HF_CACHE_DIR=./models
HF_MODEL_DIAGNOSTIC=mistralai/Mistral-7B-Instruct-v0.3
HF_MODEL_PLANNER=microsoft/phi-2
HF_MODEL_EXECUTOR=TinyLlama/TinyLlama-1.1B-Chat-v1.0
HF_MODEL_VALIDATOR=mistralai/Mistral-7B-Instruct-v0.3
EOF

  echo ""
  echo "📦 Downloading Hugging Face models (~15GB)..."
  mkdir -p ./models

  echo "  🔿 Downloading Mistral-7B-Instruct-v0.3..."
  huggingface-cli download "mistralai/Mistral-7B-Instruct-v0.3"     --cache-dir ./models     --token "$hf_token"

  echo "  🔿 Downloading Phi-2..."
  huggingface-cli download "microsoft/phi-2"     --cache-dir ./models     --token "$hf_token"

  echo "  🔿 Downloading TinyLlama-1.1B-Chat-v1.0..."
  huggingface-cli download "TinyLlama/TinyLlama-1.1B-Chat-v1.0"     --cache-dir ./models     --token "$hf_token"

  echo "✅ HF models downloaded and configured"
fi

echo ""
echo "🔐 Bitbucket Configuration"
read -p "Enter Bitbucket email/username: " bb_user
read -p "Enter Bitbucket app password: " -s bb_pass
echo ""

cat >> .env.production << EOF
BITBUCKET_USERNAME=$bb_user
BITBUCKET_APP_PASSWORD=$bb_pass
EOF

echo ""
echo "✅ Configuration complete!"
echo ""
echo "🚀 To start the agent, run:"
echo "  source venv/bin/activate"
echo "  export (cat .env.production | xargs)"
echo "  python3 -m agent.main"
echo ""
echo "🔍 To test connectivity:"
echo "  curl http://localhost:8000/health"
