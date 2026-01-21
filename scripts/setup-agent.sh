#!/bin/bash
# Lab-Verse Agent - Automated Setup with Hugging Face Token
# This script sets up the agent and uses your HF token for model downloads

set -e

echo "🚀 Lab-Verse Agent - Hugging Face Setup (No Docker)"
echo "====================================================="
echo ""

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Step 1: Check Python
echo -e "${YELLOW}1️⃣  Checking Python...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 not found. Please install Python 3.8+${NC}"
    exit 1
fi
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo -e "${GREEN}✅ Python $PYTHON_VERSION found${NC}"

# Step 2: Create virtual environment
echo -e "${YELLOW}2️⃣  Creating Python virtual environment...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
else
    echo -e "${GREEN}✅ Virtual environment already exists${NC}"
fi

source venv/bin/activate

# Step 3: Install dependencies
echo -e "${YELLOW}3️⃣  Installing Python dependencies...${NC}"
pip install --upgrade pip setuptools wheel > /dev/null 2>&1
pip install -r requirements.txt > /dev/null 2>&1
echo -e "${GREEN}✅ Dependencies installed${NC}"

# Step 4: Prompt for HF token
echo -e "${YELLOW}4️⃣  Hugging Face Authentication${NC}"
echo "Get your token from: https://huggingface.co/settings/tokens"
read -sp "Enter your Hugging Face API token (will be hidden): " HF_TOKEN
echo ""

if [ -z "$HF_TOKEN" ]; then
    echo -e "${RED}❌ No HF token provided. Models won't download without authentication.${NC}"
    echo "You can add it later to .env.production"
else
    echo -e "${GREEN}✅ HF token received${NC}"
fi

# Step 5: Prompt for Bitbucket credentials
echo ""
echo -e "${YELLOW}5️⃣  Bitbucket Configuration${NC}"
echo "Get App Password from: https://bitbucket.org/account/settings/personal-bitbucket-settings/app-passwords"
read -p "Enter Bitbucket username (email): " BB_USERNAME
read -sp "Enter Bitbucket App Password (will be hidden): " BB_PASSWORD
echo ""

if [ -z "$BB_USERNAME" ] || [ -z "$BB_PASSWORD" ]; then
    echo -e "${RED}⚠️  Bitbucket credentials incomplete. Add them to .env.production later.${NC}"
fi

# Step 6: Create .env.production
echo -e "${YELLOW}6️⃣  Creating .env.production...${NC}"
cat > .env.production << EOF
# Bitbucket Configuration
PIPELINE_PLATFORM=bitbucket
BITBUCKET_WORKSPACE=lab-verse-monitaring
BITBUCKET_USERNAME=$BB_USERNAME
BITBUCKET_APP_PASSWORD=$BB_PASSWORD

# Hugging Face Configuration
HF_TOKEN=$HF_TOKEN
HF_DEVICE=cuda
HF_LOAD_IN_8BIT=true
HF_LOAD_IN_4BIT=false
HF_CACHE_DIR=./models
HF_MODEL_DIAGNOSTIC=mistralai/Mistral-7B-Instruct-v0.3
HF_MODEL_PLANNER=microsoft/phi-2
HF_MODEL_EXECUTOR=TinyLlama/TinyLlama-1.1B-Chat-v1.0
HF_MODEL_VALIDATOR=mistralai/Mistral-7B-Instruct-v0.3

# Agent Configuration
ENVIRONMENT=production
LOG_LEVEL=INFO
MAX_RETRIES=3
ENABLE_HUMAN_APPROVAL=true
ENABLE_AUDIT_LOGGING=true
ENABLE_RATE_LIMITING=true
KUBERNETES_NAMESPACE=lab-verse-monitoring
ENABLE_METRICS=true
METRICS_PORT=8001
EOF
chmod 600 .env.production
echo -e "${GREEN}✅ .env.production created (permissions: 600)${NC}"

# Step 7: Download models
echo ""
echo -e "${YELLOW}7️⃣  Downloading Hugging Face models (~15GB)...${NC}"
echo "This may take 10-30 minutes depending on your internet speed."
echo ""

export HF_TOKEN=$HF_TOKEN

mkdir -p ./models

MODELS=(
  "mistralai/Mistral-7B-Instruct-v0.3"
  "microsoft/phi-2"
  "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
)

for model in "${MODELS[@]}"; do
    echo "📥 Downloading: $model"
    huggingface-cli download "$model" --cache-dir ./models --resume-download --local-dir-use-symlinks False
    echo -e "${GREEN}✅ Downloaded: $model${NC}"
    echo ""
done

echo -e "${GREEN}✅ All models downloaded!${NC}"
echo "📊 Model size:"
du -sh ./models
echo ""

# Step 8: Test configuration
echo -e "${YELLOW}8️⃣  Testing configuration...${NC}"
export $(cat .env.production | xargs)

python3 << 'PYTHON_EOF'
try:
    from agent.config import config
    import torch
    print("✅ Configuration loaded successfully")
    print(f"🤖 Device: {config.hf.device}")
    print(f"🧠 CUDA available: {torch.cuda.is_available()}")
    print(f"📦 Cache directory: {config.hf.hf_cache_dir}")
    print(f"🔧 8-bit quantization: {config.hf.load_in_8bit}")
    print(f"🏢 Bitbucket workspace: {config.bitbucket.workspace}")
    print(f"👤 Bitbucket user: {config.bitbucket.username}")
    print("\n✅ All configurations valid!")
except Exception as e:
    print(f"❌ Configuration error: {e}")
    import traceback
    traceback.print_exc()
PYTHON_EOF

echo ""
echo -e "${GREEN}=====================================================${NC}"
echo -e "${GREEN}✅ SETUP COMPLETE!${NC}"
echo -e "${GREEN}=====================================================${NC}"
echo ""
echo "To start the agent, run:"
echo "  source venv/bin/activate"
echo "  export \$(cat .env.production | xargs)"
echo "  python3 -m agent.main"
echo ""
echo "Then in another terminal:"
echo "  curl http://localhost:8000/health"
echo ""
