#!/bin/bash

echo "🚀 Starting All AI Services..."

# 1. Start Ollama (if not running)
if ! systemctl is-active --quiet ollama; then
    sudo systemctl start ollama
    echo "✅ Ollama started"
fi

# 2. Start LocalAI (Docker)
if ! docker ps | grep -q localai; then
    cd ~/localai
    ./start-localai.sh
    echo "✅ LocalAI started"
fi

# 3. Start Stable Diffusion (background)
if ! pgrep -f "webui.sh" > /dev/null; then
    cd ~/stable-diffusion-webui
    nohup ./webui.sh --listen --port 7861 > sd.log 2>&1 &
    echo "✅ Stable Diffusion started (check sd.log)"
fi

# 4. Wait for services to be ready
sleep 10

echo ""
echo "🎉 All services running!"
echo "📊 Service URLs:"
echo "  - Ollama:            http://localhost:11434"
echo "  - LocalAI:           http://localhost:8080"
echo "  - Stable Diffusion:  http://localhost:7861"
echo ""
echo "🧪 Test commands:"
echo "  ollama run mistral:7b-instruct"
echo "  curl http://localhost:8080/readyz"
