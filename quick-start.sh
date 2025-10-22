#!/bin/bash

# AI Content Creation Suite - Quick Start Script

set -e

echo "🚀 AI Content Creation Suite - Quick Start"
echo "=========================================="
echo ""

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18+ first."
    echo "   Visit: https://nodejs.org/"
    exit 1
fi

# Check Node.js version
NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 18 ]; then
    echo "❌ Node.js 18+ is required. Current version: $(node -v)"
    exit 1
fi

echo "✅ Node.js $(node -v) detected"

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "❌ npm is not installed. Please install npm first."
    exit 1
fi

echo "✅ npm $(npm -v) detected"

# Install dependencies
echo ""
echo "📦 Installing dependencies..."
npm install

# Run setup
echo ""
echo "🔧 Running setup..."
npm run setup

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo ""
    echo "⚠️  .env file not found. Creating from template..."
    cp .env.example .env
    echo "✅ .env file created. Please configure your API keys."
fi

# Check if Redis is running (optional)
if command -v redis-cli &> /dev/null; then
    if redis-cli ping &> /dev/null; then
        echo "✅ Redis is running"
    else
        echo "⚠️  Redis is not running. Caching will be disabled."
        echo "   To start Redis: redis-server"
    fi
else
    echo "⚠️  Redis not found. Caching will be disabled."
    echo "   Install Redis for better performance: https://redis.io/"
fi

echo ""
echo "🎉 Setup completed successfully!"
echo ""
echo "Next steps:"
echo "1. Edit .env file and add your API keys:"
echo "   - OPENAI_API_KEY=your_key_here"
echo "   - GOOGLE_API_KEY=your_key_here"
echo "   - ZAI_API_KEY=your_key_here"
echo "   - API_KEY=your_secure_api_key"
echo ""
echo "2. Start the application:"
echo "   npm start"
echo ""
echo "3. Open your browser:"
echo "   http://localhost:3000"
echo ""
echo "For Docker deployment:"
echo "   docker-compose up -d"
echo ""
echo "Happy content creating! 🎨"