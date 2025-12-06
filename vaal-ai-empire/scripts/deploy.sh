#!/bin/bash

# vaal-ai-empire/scripts/deploy.sh
# This script prepares and runs the application in a local environment.

set -e

echo "Starting local deployment..."

# Step 1: Install Python dependencies
echo "Installing Python dependencies..."
pip install -r vaal-ai-empire/requirements.txt

# Step 2: Install Node.js dependencies
echo "Installing Node.js dependencies..."
npm install --prefix vaal-ai-empire

# Step 3: Run the Tax Collector agent to fetch articles
echo "Starting the Tax Collector agent..."
python3 vaal-ai-empire/src/agents/tax-collector.py

# Step 4: Create the semantic search index
echo "Creating the semantic search index..."
python3 vaal-ai-empire/src/agents/semantic-search.py

echo "Deployment complete! The system is now running locally."
