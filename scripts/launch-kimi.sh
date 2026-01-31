#!/bin/bash
set -e

echo "🚀 Launching Kimi CLI..."

# Build the Docker image if it doesn't exist
docker-compose -f docker-compose.kimi.yml build

# Run the Kimi CLI in the container
docker-compose -f docker-compose.kimi.yml run --rm kimi-cli kimi "$@"
