#!/bin/bash
set -e

cd ~/stable-diffusion-webui

# Start WebUI
./webui.sh --listen --port 7861

echo "🎨 Stable Diffusion running on http://localhost:7861"
