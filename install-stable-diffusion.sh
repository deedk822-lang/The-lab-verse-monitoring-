#!/bin/bash
set -e

echo "🎨 Installing Stable Diffusion WebUI..."

# Clone repository
cd ~
git clone https://github.com/AUTOMATIC1111/stable-diffusion-webui.git
cd stable-diffusion-webui

# Install
./webui.sh --skip-torch-cuda-test

echo "✅ Stable Diffusion installed!"
