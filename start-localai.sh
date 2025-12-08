#!/bin/bash
set -e

cd ~/localai

# Start LocalAI on port 8080
docker run -d \
  --name localai \
  -p 8080:8080 \
  -v $PWD/models:/models \
  -v $PWD/images:/tmp/generated/images \
  --restart=always \
  quay.io/go-skynet/local-ai:latest

echo "🚀 LocalAI running on http://localhost:8080"
echo "📊 Health check: curl http://localhost:8080/readyz"
