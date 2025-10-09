#!/bin/bash
# scripts/install-kimi.sh

echo "🤖 Installing Kimi Project Manager..."
echo "====================================="

# Check if OpenAI API key is set
if [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️  Warning: OPENAI_API_KEY environment variable is not set."
    echo "Kimi may have limited functionality without it."
fi

# Build Kimi Docker image
echo "🏗️  Building Kimi Docker image..."
docker build -f Dockerfile.kimi -t labverse/kimi-manager:latest .

if [ $? -eq 0 ]; then
    echo "✅ Kimi Project Manager Docker image built successfully!"
    echo ""
    echo "🚀 Next steps:"
    echo "1. If you have an OpenAI API key, set it: export OPENAI_API_KEY='your-key-here'"
    echo "2. Start the Kimi service: docker-compose -f docker-compose.kimi.yml up -d"
    echo "3. Check the service logs: docker logs labverse_kimi_pm"
    echo "4. Access Kimi API at: http://localhost:8084"
    echo "5. Use the CLI: python -m src.kimi_instruct.cli status"
    echo ""
    echo "🎯 Kimi is ready to manage your monitoring project!"
else
    echo "❌ Error: Docker image build failed."
    exit 1
fi