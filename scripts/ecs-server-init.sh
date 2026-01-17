#!/bin/bash
# scripts/ecs-server-init.sh
# One-time setup script for Alibaba Cloud ECS (Ubuntu)
# Usage: curl https://raw.githubusercontent.com/.../scripts/ecs-server-init.sh | bash

set -euo pipefail

echo "🚀 Initializing Rainmaker Superstack on Alibaba ECS..."
echo "================================================================"

# --- 1. System Updates ---
echo "[1/6] Updating system packages..."
sudo apt-get update -qq
sudo apt-get upgrade -y -qq

# --- 2. Install Docker ---
echo "[2/6] Installing Docker Engine..."
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# --- 3. Install Docker Compose ---
echo "[3/6] Installing Docker Compose..."
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# --- 4. Install Git ---
echo "[4/6] Installing Git..."
sudo apt-get install -y git

# --- 5. Configure Firewall (Security) ---
echo "[5/6] Configuring UFW..."
# Allow SSH
sudo ufw allow 22/tcp
# Allow Web Server (8080)
sudo ufw allow 8080/tcp
# Allow Monitoring (9090)
sudo ufw allow 9090/tcp
sudo ufw --force enable

# --- 6. Clone Repository ---
echo "[6/6] Cloning The-Lab-Verse-Monitoring Repository..."
mkdir -p /app
cd /app
git clone https://github.com/deedk822-lang/The-lab-verse-monitoring-.git

# --- 7. Setup Environment ---
echo "[7/9] Creating Environment Template..."
cd /app/The-lab-verse-monitoring-
if [ ! -f .env ]; then
  cp .env.example .env
  echo "⚠️  IMPORTANT: Edit .env file and add your secrets manually."
fi

# --- 8. Start Services ---
echo "[8/9] Starting Docker Compose Stack..."
cd /app/The-lab-verse-monitoring-
docker-compose pull
docker-compose up -d

# --- 9. Health Check ---
echo "[9/9] Waiting for services to start..."
sleep 15
curl -f http://localhost:8080/health || echo "⚠️  Health check failed immediately. Docker might still be booting."

echo "================================================================"
echo "✅ Server Initialization Complete."
echo "Next Steps:"
echo "1. Configure Environment: nano /app/The-lab-verse-monitoring-/.env"
echo "2. Restart Services: cd /app/The-lab-verse-monitoring- && docker-compose restart"
echo "3. Check Logs: docker-compose logs -f"
