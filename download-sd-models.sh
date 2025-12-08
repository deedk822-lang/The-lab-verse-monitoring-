#!/bin/bash
set -e

cd ~/stable-diffusion-webui/models/Stable-diffusion

echo "📥 Downloading Stable Diffusion models..."

# SDXL (best quality)
wget -c https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/resolve/main/sd_xl_base_1.0.safetensors

# SD 1.5 (faster)
wget -c https://huggingface.co/runwayml/stable-diffusion-v1-5/resolve/main/v1-5-pruned-emaonly.safetensors

echo "✅ SD models downloaded!"
