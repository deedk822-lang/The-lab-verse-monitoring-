#!/bin/bash
set -e

echo "🌅 WAKING UP THE VAAL AI EMPIRE..."
echo "   - Region: Singapore (ap-southeast-1)"
echo "   - Supervisor: Qwen-Max"
echo "   - Status: LIVE"

# 1. CONFIGURE ALIBABA CLOUD (SINGAPORE)
# Using the keys you provided: ACCESS_KEY_ID / ACCESS_KEY_SECRET
export ALIBABA_CLOUD_ACCESS_KEY_ID="$ACCESS_KEY_ID"
export ALIBABA_CLOUD_ACCESS_KEY_SECRET="$ACCESS_KEY_SECRET"
export ALIBABA_CLOUD_REGION_ID="ap-southeast-1"

# Configure the CLI for underlying system calls
if command -v aliyun &> /dev/null; then
    aliyun configure set \
        --profile default \
        --region $ALIBABA_CLOUD_REGION_ID \
        --access-key-id $ALIBABA_CLOUD_ACCESS_KEY_ID \
        --access-key-secret $ALIBABA_CLOUD_ACCESS_KEY_SECRET
    echo "✅ Aliyun CLI configured for Singapore."
fi

# 2. INJECT ENVIRONMENT VARIABLES (MAPPING SECRETS)
# The Python scripts expect specific variable names. We map your secrets to them here.

# --- CORE INTELLIGENCE ---
export DASHSCOPE_API_KEY="$DASHSCOPE_API_KEY"  # Qwen-Max Brain

# --- MEMORY (OSS VAULT - SINGAPORE) ---
export OSS_ACCESS_KEY_ID="$ACCESS_KEY_ID"
export OSS_ACCESS_KEY_SECRET="$ACCESS_KEY_SECRET"
export OSS_ENDPOINT="https://oss-ap-southeast-1.aliyuncs.com"
export OSS_BUCKET="vaal-vault"

# --- DEPARTMENT HEADS ---
export MISTRAL_API_KEY="$MISTRALAI_API_KEY"    # Content Dept
export COHERE_API_KEY="$COHERE_API_KEY"        # Vision/Rerank Dept
export HF_TOKEN="$HUGGINGFACE_API_KEY"         # Factory Dept
export BRIA_API_KEY="$BRIA_API_KEY"            # FIBO/Image Engine

# --- NOTIFICATIONS ---
# Using standard SMTP logic from your secrets if available, or logging to OSS
export SMTP_USER="$USER_LOGON_NAME"
# export SMTP_PASS="$SMTP_PASSWORD" # You'll need to set this manually or via secrets

# 3. VERIFY & INSTALL PRODUCTION DEPENDENCIES
echo "📦 Verifying Neural Link (Dependencies)..."
pip install qwen-agent oss2 mistralai cohere pandas python-dotenv dashscope huggingface_hub pypdf --upgrade --quiet

# 4. WAKE UP THE SUPERVISOR (THE BRAIN)
echo "🧠 ACTIVATING EMPIRE SUPERVISOR..."

python3 scripts/live_check.py

# 5. START THE BACKGROUND WORKER (THE REVENUE LOOP)
echo "💸 STARTING REVENUE NOTIFICATION WORKER..."
# Runs in the background using nohup to keep alive after you disconnect
nohup python3 scripts/notification_worker.py > logs/worker.log 2>&1 &
echo "✅ Worker running (PID: $!) - Monitoring OSS for Revenue Triggers."
