#!/bin/bash
set -euo pipefail

# Build all services
echo "Building all services..."
sudo docker compose -f docker-compose.production.yml build

# Start infrastructure services first
echo "Starting infrastructure services (PostgreSQL and Redis)..."
sudo docker compose -f docker-compose.production.yml up -d postgres redis

# Wait for databases to be ready
echo "Waiting for databases to be ready..."
sleep 10

# Start all services
echo "Starting all services..."
sudo docker compose -f docker-compose.production.yml up -d

echo "All services started. You can view logs with:"
echo "sudo docker compose -f docker-compose.production.yml logs -f"
echo ""
echo "You can check service status with:"
echo "sudo docker compose -f docker-compose.production.yml ps"
