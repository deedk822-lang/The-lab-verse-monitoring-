#!/bin/bash
set -e

echo "🖼️ Installing Qwen-VL..."

# Create environment
mkdir -p ~/qwen-vl
cd ~/qwen-vl
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
pip install transformers accelerate sentencepiece pillow

# Clone Qwen-VL
git clone https://github.com/QwenLM/Qwen-VL.git
cd Qwen-VL

echo "✅ Qwen-VL installed!"
