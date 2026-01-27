#!/bin/bash
set -e
echo "🏗️ Installing Glean/Context Dependencies..."
pip install mcp databricks-sdk httpx --upgrade --quiet
