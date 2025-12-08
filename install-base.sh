#!/bin/bash
set -e

echo "🔧 Installing base dependencies..."

# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.11
sudo apt install -y python3.11 python3.11-venv python3.11-dev
sudo apt install -y python3-pip

# Install build tools
sudo apt install -y build-essential git curl wget

# Install Docker (for containerized models)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo apt install -y docker-compose

echo "✅ Base dependencies installed!"
echo "⚠️  Please logout and login again for Docker permissions to take effect"
