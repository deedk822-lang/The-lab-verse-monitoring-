#!/bin/bash
# Lab-Verse Agent - Setup for Google Colab
# Run this in a Colab cell: !bash scripts/setup-colab.sh

echo "🚀 Lab-Verse Agent - Colab Setup"
echo "================================"

# Install system dependencies
echo "💾 Installing system packages..."
apt-get update > /dev/null 2>&1
apt-get install -y git curl > /dev/null 2>&1

# Clone or navigate to repo
if [ ! -d "lab-verse-monitoring-agent" ]; then
    echo "📐 Cloning repository..."
    git clone https://github.com/deedk822-lang/The-lab-verse-monitoring-.git lab-verse-monitoring-agent
fi

cd lab-verse-monitoring-agent

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -q -r requirements.txt

# Create .env for Colab
echo "📜 Creating .env.colab..."
cat > .env.colab << 'EOF'
BITBUCKET_WORKSPACE=lab-verse-monitaring
BITBUCKET_USERNAME=your-email@atlassian.com
BITBUCKET_APP_PASSWORD=your-app-password

HF_TOKEN=
HF_DEVICE=cuda
HF_LOAD_IN_8BIT=true
HF_CACHE_DIR=/content/models

ENVIRONMENT=production
LOG_LEVEL=INFO
EOF

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Update .env.colab with your credentials"
echo "2. Run: bash scripts/download-models-colab.sh"
echo "3. Run: python -m agent.main"
