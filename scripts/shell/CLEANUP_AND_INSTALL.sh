#!/bin/bash

# CLEANUP_AND_INSTALL.sh
# Complete cleanup and fresh installation script for The Lab Verse Monitoring

set -e  # Exit on error

echo "🧹 Starting complete cleanup..."

# 1. Clean Node.js artifacts
echo "📦 Removing Node.js artifacts..."
rm -rf node_modules
rm -f package-lock.json
rm -f yarn.lock
rm -f pnpm-lock.yaml
rm -rf .npm
rm -rf .yarn

# 2. Clean Python artifacts
echo "🐍 Removing Python artifacts..."
find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
find . -type d -name "build" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name "dist" -exec rm -rf {} + 2>/dev/null || true
rm -rf venv
rm -rf .venv

# 3. Clean build artifacts
echo "🔨 Removing build artifacts..."
rm -rf .next
rm -rf out
rm -rf dist
rm -rf build
rm -rf .turbo

# 4. Clean cache directories
echo "💾 Clearing caches..."
rm -rf .cache
rm -rf .eslintcache
rm -rf .prettierignore
npm cache clean --force 2>/dev/null || true

echo "✅ Cleanup complete!"
echo ""
echo "📥 Installing fresh dependencies..."
echo ""

# 5. Install Node.js dependencies
echo "📦 Installing Node.js packages..."
if command -v npm &> /dev/null; then
    npm install
    echo "✅ Node.js packages installed"
else
    echo "⚠️  npm not found, skipping Node.js installation"
fi

echo ""

# 6. Install Python dependencies
echo "🐍 Installing Python packages..."
if command -v python3 &> /dev/null; then
    # Create virtual environment
    python3 -m venv venv
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip setuptools wheel
    
    # Install requirements
    if [ -f "requirements.txt" ]; then
        pip install --no-cache-dir -r requirements.txt
        echo "✅ Python packages installed"
    else
        echo "⚠️  requirements.txt not found"
    fi
    
    deactivate
else
    echo "⚠️  python3 not found, skipping Python installation"
fi

echo ""
echo "🎉 Installation complete!"
echo ""
echo "Next steps:"
echo "  1. Activate Python virtual environment: source venv/bin/activate"
echo "  2. Start the server: npm start"
echo "  3. Run tests: npm test"
echo ""
