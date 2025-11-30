#!/bin/bash

# Lab-Verse Hybrid AI Testing Script
# Tests LocalAI + Perplexity routing and cost optimization

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_test() {
    echo -e "${BLUE}🧪 Testing: $1${NC}"
}

print_result() {
    echo -e "${GREEN}✅ Result: $1${NC}"
}

print_cost() {
    echo -e "${YELLOW}💰 Cost: $1${NC}"
}

# Configuration
N8N_URL="http://localhost:5678"
HYBRID_ENDPOINT="$N8N_URL/webhook/hybrid-ai"

echo "🤖 Lab-Verse Hybrid AI Test Suite"
echo "====================================="
echo "Testing LocalAI + Perplexity intelligent routing..."
echo ""

# Test 1: General Query (should route to LocalAI)
print_test "General query routing to LocalAI"
response1=$(curl -s -X POST "$HYBRID_ENDPOINT" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Explain machine learning basics"
  }')

if echo "$response1" | jq -e '.provider_used == "localai"' > /dev/null; then
    print_result "Correctly routed to LocalAI"
    cost1=$(echo "$response1" | jq -r '.cost_usd // 0')
    print_cost "$cost1 (Expected: $0.00)"
else
    echo -e "${RED}❌ Unexpected routing${NC}"
fi
echo ""

# Test 2: Real-time Query (should route to Perplexity)
print_test "Real-time query routing to Perplexity"
response2=$(curl -s -X POST "$HYBRID_ENDPOINT" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Latest AI news today 2025",
    "require_sources": true
  }')

if echo "$response2" | jq -e '.provider_used == "perplexity"' > /dev/null; then
    print_result "Correctly routed to Perplexity"
    sources=$(echo "$response2" | jq -r '.sources | length')
    cost2=$(echo "$response2" | jq -r '.cost_usd // 0')
    print_result "Sources found: $sources"
    print_cost "$cost2 (Expected: ~$0.0002)"
else
    echo -e "${RED}❌ Unexpected routing or Perplexity unavailable${NC}"
    echo "Response: $(echo $response2 | jq -r '.provider_used // "unknown"')"
fi
echo ""

# Test 3: Code Query (should route to LocalAI) 
print_test "Code query routing to LocalAI (privacy)"
response3=$(curl -s -X POST "$HYBRID_ENDPOINT" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Debug this JavaScript function: function add(a, b) { return a + b + c; }"
  }')

if echo "$response3" | jq -e '.provider_used == "localai"' > /dev/null; then
    print_result "Correctly routed to LocalAI (kept code private)"
    privacy_score=$(echo "$response3" | jq -r '.privacy_score // 0')
    cost3=$(echo "$response3" | jq -r '.cost_usd // 0')
    print_result "Privacy score: $privacy_score/100"
    print_cost "$cost3 (Expected: $0.00)"
else
    echo -e "${RED}❌ Code should stay local for privacy${NC}"
fi
echo ""

# Test 4: Research Query (should route to Perplexity)
print_test "Research query routing to Perplexity"
response4=$(curl -s -X POST "$HYBRID_ENDPOINT" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Compare React vs Vue.js performance benchmarks 2025", 
    "include_analysis": true
  }')

if echo "$response4" | jq -e '.provider_used == "perplexity"' > /dev/null; then
    print_result "Correctly routed to Perplexity for research"
    cost4=$(echo "$response4" | jq -r '.cost_usd // 0')
    print_cost "$cost4 (Expected: ~$0.0003)"
else
    echo -e "${YELLOW}⚠️  Research routed to $(echo $response4 | jq -r '.provider_used // "unknown"') instead${NC}"
fi
echo ""

# Test 5: System Query (should route to LocalAI)
print_test "System query routing to LocalAI (internal)"
response5=$(curl -s -X POST "$HYBRID_ENDPOINT" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Check Lab-Verse system health status"
  }')

if echo "$response5" | jq -e '.provider_used == "localai"' > /dev/null; then
    print_result "Correctly routed to LocalAI (internal query)"
    cost5=$(echo "$response5" | jq -r '.cost_usd // 0')
    print_cost "$cost5 (Expected: $0.00)"
else
    echo -e "${RED}❌ System queries should stay internal${NC}"
fi
echo ""

# Calculate total cost savings
total_cost=$(echo "$cost1 + $cost2 + $cost3 + $cost4 + $cost5" | bc -l 2>/dev/null || echo "0")
cloud_only_cost=0.025  # Estimated cost if all went to premium cloud
savings=$(echo "$cloud_only_cost - $total_cost" | bc -l 2>/dev/null || echo "0")
savings_percent=$(echo "scale=1; ($savings / $cloud_only_cost) * 100" | bc -l 2>/dev/null || echo "0")

echo "====================================="
echo -e "${GREEN}📈 HYBRID AI TEST RESULTS${NC}"
echo "====================================="
echo -e "Total Cost: ${YELLOW}\$$total_cost${NC}"
echo -e "vs Cloud-Only: ${RED}\$$cloud_only_cost${NC}"
echo -e "Savings: ${GREEN}\$$savings ($savings_percent%)${NC}"
echo ""
echo "Provider Usage:"
echo "- LocalAI: $(echo "$response1 $response3 $response5" | grep -o '"localai"' | wc -l)/3 queries (Expected: 3/3)"
echo "- Perplexity: $(echo "$response2 $response4" | grep -o '"perplexity"' | wc -l)/2 queries (Expected: 2/2)"
echo ""
print_result "Hybrid AI system test completed!"

# Optional: Save detailed results
cat > hybrid_test_results.json << EOF
{
  "timestamp": "$(date -Iseconds)",
  "tests": {
    "general_query": $response1,
    "realtime_query": $response2, 
    "code_query": $response3,
    "research_query": $response4,
    "system_query": $response5
  },
  "cost_analysis": {
    "total_cost": $total_cost,
    "cloud_only_cost": $cloud_only_cost,
    "savings": $savings,
    "savings_percent": $savings_percent
  }
}
EOF

print_result "Detailed results saved to: hybrid_test_results.json"