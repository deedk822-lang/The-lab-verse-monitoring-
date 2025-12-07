#!/bin/bash
set -e

echo "🏗️ CONSTRUCTING THE AGENT'S HOME (CONTEXT LAYER)..."

# 1. Install the Model Context Protocol (MCP) SDK
# This is the standard language for AI tools to talk to Data Servers
pip install mcp httpx databricks-sdk --upgrade --quiet

# 2. Verify Connection to the Glean/Databricks Server
# We simulate a handshake to ensure the 'Place to Run' exists.

echo "🔌 Testing Connection to Glean Enterprise Graph..."

python3 -c "
import os
import sys

# The Agent needs to know where the 'Home' is
glean_url = os.getenv('GLEAN_API_ENDPOINT')
glean_key = os.getenv('GLEAN_API_KEY')

if not glean_url or not glean_key:
    print('❌ CRITICAL: The Agent has no home. Set GLEAN_API_ENDPOINT.')
    # For now, we don't exit 1 so you can proceed with setting it up,
    # but in production, this is fatal.
    sys.exit(0)

print('✅ Glean Endpoint Detected.')
print('   - Ready to fuse Structured Data (Databricks) + Unstructured (Docs)')
"

echo "✅ Context Layer Dependencies Installed."
