#!/bin/bash
set -e

cd ~/qwen-vl/Qwen-VL
source ../venv/bin/activate

# Run Qwen-VL server
python web_demo.py --port 7860

echo "🚀 Qwen-VL running on http://localhost:7860"
