#!/bin/bash
set -e

# Change to the script's directory to ensure paths are relative to the plugin root
cd "$(dirname "$0")"

echo "🔧 Setting up Dev-Ops Suite..."

# 1. Install Python Dependencies
if [ -f "servers/requirements.txt" ]; then
    echo "📦 Installing MCP dependencies..."
    pip3 install -r servers/requirements.txt
fi

# 2. Verify Plugin Structure
if [ ! -f ".claude-plugin/plugin.json" ]; then
    echo "❌ Error: plugin.json missing!"
    exit 1
fi

echo "✅ Setup Complete. Restart Claude Code to load the 'dev-ops-suite'."
