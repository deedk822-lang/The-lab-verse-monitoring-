#!/bin/bash
set -e

echo "🧪 Testing MCP Gateways"
echo ""

# Load environment
source .env

# Test HuggingFace
echo "1️⃣ Testing HuggingFace Gateway..."
curl -X POST "$GATEWAY_URL/mcp/huggingface/messages" \
  -H "Authorization: Bearer $GATEWAY_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "hf-mcp",
    "messages": [{"role":"user","content":"hf_list_models {\"search\":\"gpt2\"}"}]
  }' | jq .

echo ""

# Test SocialPilot
echo "2️⃣ Testing SocialPilot Gateway..."
curl -X POST "$GATEWAY_URL/mcp/socialpilot/messages" \
  -H "Authorization: Bearer $GATEWAY_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "socialpilot-mcp",
    "messages": [{"role":"user","content":"sp_list_accounts {}"}]
  }' | jq .

echo ""

# Test Unito
echo "3️⃣ Testing Unito Gateway..."
curl -X POST "$GATEWAY_URL/mcp/unito/messages" \
  -H "Authorization: Bearer $GATEWAY_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "unito-mcp",
    "messages": [{"role":"user","content":"unito_list_workspaces {}"}]
  }' | jq .

echo ""

# Test WordPress.com
echo "4️⃣ Testing WordPress.com Gateway..."
curl -X POST "$GATEWAY_URL/mcp/wpcom/messages" \
  -H "Authorization: Bearer $GATEWAY_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "wpcom-mcp",
    "messages": [{"role":"user","content":"wpcom_list_sites {}"}]
  }' | jq .

echo ""
echo "✅ All tests complete!"
