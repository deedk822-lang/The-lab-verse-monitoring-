#!/bin/bash
# scripts/ecs-server-init.sh
# One-time setup script for Alibaba Cloud ECS (Ubuntu)
# Usage: curl https://raw.githubusercontent.com/deedk822-lang/The-lab-verse-monitoring-/main/scripts/ecs-server-init.sh | bash
set -euo pipefail
trap 'echo "Error at line $LINENO"' ERR

echo "🚀 Initializing Rainmaker Superstack on Alibaba ECS..."
echo "================================================================"

# --- 1. System Update ---
echo "[1/6] Updating system packages..."
sudo apt-get update -y
sudo apt-get upgrade -y

# --- 2. Install Docker & Docker Compose ---
echo "[2/6] Installing Docker and Docker Compose..."
sudo apt-get install -y docker.io
sudo systemctl start docker
sudo systemctl enable docker
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
sudo usermod -aG docker $USER

# --- 3. Install Git ---
echo "[3/6] Installing Git..."
sudo apt-get install -y git

# --- 4. Configure Firewall (UFW) ---
echo "[4/6] Configuring firewall..."
if ! command -v ufw &> /dev/null; then
    sudo apt-get install -y ufw
fi
sudo ufw --force enable
sudo ufw allow 22/tcp  # SSH
sudo ufw allow 80/tcp  # HTTP
sudo ufw allow 443/tcp # HTTPS
sudo ufw allow 8000/tcp # Application Port

# --- 5. Install Alibaba Cloud CLI ---
echo "[5/6] Installing Alibaba Cloud CLI..."
curl -sL https://aliyuncli.alicdn.com/aliyun-cli-linux-latest-amd64.zip -o aliyun-cli.zip
unzip aliyun-cli.zip
sudo mv aliyun /usr/local/bin

# --- 6. Clone Repository ---
echo "[6/6] Cloning The-Lab-Verse-Monitoring Repository..."
mkdir -p /app
cd /app
git clone https://github.com/deedk822-lang/The-lab-verse-monitoring-.git

echo "✅ Initialization complete. Please reboot the server."
