#!/bin/bash
set -e

echo "🤗 DEPLOYING HUGGING FACE TRANSFORMERS CORE..."
echo "   - Library: Transformers + PyTorch (CPU Optimized)"
echo "   - Purpose: Local Intelligence & Offline Capability"

# 1. UPDATE REQUIREMENTS
# We append these critical libraries to your master list.
cat << 'EOF' >> vaal-ai-empire/requirements.txt
transformers>=4.30.0
torch>=2.0.0
accelerate>=0.20.0
EOF

# 2. INSTALLATION (The Heavy Lift)
# We use the CPU index URL to ensure it doesn't try to download 3GB of CUDA drivers on a non-GPU machine.
echo "📦 Installing Neural Engine (This may take a minute)..."
pip cache purge
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu --upgrade --quiet
pip install transformers accelerate --upgrade --quiet

# 3. VERIFICATION (The "Spark" Test)
# This runs the exact Python test code from the Hugging Face docs you provided.
echo "⚡ RUNNING NEURAL DIAGNOSTIC..."

python3 -c "
import sys
try:
    from transformers import pipeline

    # Suppress warnings for cleaner output
    import logging
    logging.getLogger('transformers').setLevel(logging.ERROR)

    print('   > Loading Sentiment Analysis Pipeline (Local Model)...')
    classifier = pipeline('sentiment-analysis')

    # The Test Input
    text = 'hugging face is the best'
    result = classifier(text)

    print(f'   > Input: \"{text}\"')
    print(f'   > Output: {result}')
    print('✅ TRANSFORMERS ENGINE ONLINE.')

except Exception as e:
    print(f'❌ ENGINE FAILURE: {e}')
    sys.exit(1)
"

echo "✅ INSTALLATION COMPLETE."
echo "   - Your Agent now has a Local Brain."
