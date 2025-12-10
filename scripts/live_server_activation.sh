#!/bin/bash
set -e

echo "🔌 CONNECTING TO MOTHERSHIP (GITHUB)..."

# 1. PULL THE NEW LOGIC
# We ensure we are on main and have the latest "Real Logic" you just merged.
git checkout main
git pull origin main
echo "✅ Codebase Synced: Production Version."

# 2. CONFIGURE ENVIRONMENT (Mapping your Secrets)
# We export the keys you provided so the Python scripts can see them.
echo "🔑 Injecting Neural Keys..."

# Alibaba Cloud (Singapore)
export ALIBABA_CLOUD_ACCESS_KEY_ID="$ACCESS_KEY_ID"
export ALIBABA_CLOUD_ACCESS_KEY_SECRET="$ACCESS_KEY_SECRET"
export ALIBABA_CLOUD_REGION_ID="ap-southeast-1"

# The Brains
export DASHSCOPE_API_KEY="$DASHSCOPE_API_KEY"   # Qwen
export MISTRAL_API_KEY="$MISTRALAI_API_KEY"     # Mistral
export COHERE_API_KEY="$COHERE_API_KEY"         # Aya/Cohere
export HUGGINGFACE_API_KEY="$HUGGINGFACE_API_KEY"

# The Vault
export OSS_ACCESS_KEY_ID="$ACCESS_KEY_ID"
export OSS_ACCESS_KEY_SECRET="$ACCESS_KEY_SECRET"
export OSS_ENDPOINT="https://oss-ap-southeast-1.aliyuncs.com"
export OSS_BUCKET="vaal-vault"

# 3. INSTALL DRIVERS
echo "📦 Verifying Python Dependencies..."
pip install -r vaal-ai-empire/requirements.txt --upgrade --quiet
# Ensure the package is installed in editable mode
pip install -e vaal-ai-empire/ --quiet

# 4. WAKE UP THE EMPIRE
echo "🚀 EXECUTING WAKE_UP_EMPIRE.SH..."

if [ -f "vaal-ai-empire/scripts/wake_up_empire.sh" ]; then
    bash vaal-ai-empire/scripts/wake_up_empire.sh
else
    # Fallback if the script moved during the restructure
    echo "⚠️ Wake up script not found in expected path. Launching Supervisor directly..."
    python3 vaal-ai-empire/src/core/empire_supervisor.py
fi
