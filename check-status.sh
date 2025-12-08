#!/bin/bash

echo "📊 AI Services Status"
echo "===================="

# Ollama
if systemctl is-active --quiet ollama; then
    echo "✅ Ollama: Running"
    ollama list | head -5
else
    echo "❌ Ollama: Not running"
fi

# LocalAI
if docker ps | grep -q localai; then
    echo "✅ LocalAI: Running"
    curl -s http://localhost:8080/readyz || echo "Not responding"
else
    echo "❌ LocalAI: Not running"
fi

# Stable Diffusion
if pgrep -f "webui.sh" > /dev/null; then
    echo "✅ Stable Diffusion: Running"
else
    echo "❌ Stable Diffusion: Not running"
fi

# Qwen-VL
if pgrep -f "web_demo.py" > /dev/null; then
    echo "✅ Qwen-VL: Running"
else
    echo "❌ Qwen-VL: Not running"
fi
