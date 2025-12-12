#!/bin/bash
set -e

echo "🔥 IGNITING LOCAL AI EMPIRE (SOVEREIGN NODE)..."
echo "   - Engine: LocalAI (AIO Image)"
echo "   - Capabilities: Text, Vision, Audio, Embeddings"
echo "   - Cost: $0.00/token"

# 1. STOP OLD INSTANCES
# We ensure a clean slate so ports don't clash.
docker stop vaal-local-ai 2>/dev/null || true
docker rm vaal-local-ai 2>/dev/null || true

# 2. START THE WHALE (LocalAI AIO)
# We use the 'aio-cpu' image which comes pre-configured with basics.
# If you have an Nvidia GPU, change 'cpu' to 'gpu-nvidia-cuda-12'
echo "🐳 Launching Container (Port 8080)..."

docker run -d \
  --name vaal-local-ai \
  --restart always \
  -p 8080:8080 \
  -v $PWD/models:/build/models \
  -e THREADS=4 \
  -e CONTEXT_SIZE=2048 \
  localai/localai:latest-aio-cpu

echo "⏳ Waiting for Brain to Initialize (This takes ~60 seconds)..."
# We loop until the health endpoint responds
until curl -s -f "http://localhost:8080/readyz" > /dev/null; do
    echo -n "."
    sleep 5
done
echo "✅ LocalAI is UP and READY."

# 3. VERIFY CAPABILITIES (The "Try it out" Phase)
echo "🧪 RUNNING LIVE DIAGNOSTICS..."

# TEST A: TEXT GENERATION (Strategy)
echo "   > Testing Cortex (Text Gen)..."
TEXT_RESPONSE=$(curl -s http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{ "model": "gpt-4", "messages": [{"role": "user", "content": "State your directive."}], "temperature": 0.1 }')

if [[ $TEXT_RESPONSE == *"content"* ]]; then
    echo "     ✅ Text Gen: ACTIVE"
else
    echo "     ❌ Text Gen: FAILED ($TEXT_RESPONSE)"
fi

# TEST B: EMBEDDINGS (RAG)
echo "   > Testing Memory (Embeddings)..."
EMBED_RESPONSE=$(curl -s http://localhost:8080/v1/embeddings \
  -H "Content-Type: application/json" \
  -d '{ "input": "Revenue Data", "model": "text-embedding-ada-002" }')

if [[ $EMBED_RESPONSE == *"embedding"* ]]; then
    echo "     ✅ Embeddings: ACTIVE"
else
    echo "     ❌ Embeddings: FAILED"
fi

# 4. WIRE INTO PYTHON CORE
# We update the Universal Gateway to point to localhost by default.

cat << 'EOF' > vaal-ai-empire/src/core/universal_gateway.py
import os
import logging
import httpx
from openai import OpenAI

logger = logging.getLogger("UniversalGateway")

class ModelGateway:
    def __init__(self):
        # 1. LOCAL SOVEREIGN NODE (Default)
        self.local_client = OpenAI(base_url="http://localhost:8080/v1", api_key="sk-local")

        # 2. CLOUD BACKUP (Alibaba/DeepSeek)
        self.cloud_key = os.getenv("DASHSCOPE_API_KEY")
        self.cloud_client = OpenAI(
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            api_key=self.cloud_key
        ) if self.cloud_key else None

    def generate(self, prompt, model="gpt-4", force_cloud=False):
        """
        Smart Routing:
        - If 'force_cloud' is False, use LocalAI (Free).
        - If LocalAI fails, fallback to Cloud (Paid).
        """
        if not force_cloud:
            try:
                logger.info(f"🖥️  LOCAL EXECUTION ({model})...")
                return self.local_client.chat.completions.create(
                    model=model, # LocalAI maps 'gpt-4' to its internal model
                    messages=[{"role": "user", "content": prompt}]
                ).choices[0].message.content
            except Exception as e:
                logger.warning(f"⚠️  Local Node Offline: {e}. Switching to Cloud...")

        # Cloud Fallback
        if self.cloud_client:
            logger.info("☁️  CLOUD EXECUTION (Qwen)...")
            return self.cloud_client.chat.completions.create(
                model="qwen-max",
                messages=[{"role": "user", "content": prompt}]
            ).choices[0].message.content

        return "❌ ALL SYSTEMS DOWN."
EOF

echo "✅ EMPIRE WIRED TO LOCALHOST."
echo "   - Endpoint: http://localhost:8080"
echo "   - Fallback: Alibaba Cloud"
echo "   - Status: READY FOR OFFLINE REVENUE."
