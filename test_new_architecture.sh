#!/bin/bash

echo "🚀 Testing New Architecture Endpoints..."

sleep 5 # Wait for the server to start

echo "1️⃣  Testing Model Provisioning API..."
curl -X POST http://localhost:3000/api/models/provision \
  -H "Content-Type: application/json" \
  -d '{"location": "Sebokeng", "task": "content_generation", "urgency": "high"}'
echo "\n"

echo "2️⃣  Testing Model Orchestrator API..."
curl -X POST http://localhost:3000/api/orchestrator \
  -H "Content-Type: application/json" \
  -d '{"task": "content_generation", "location": "Sebokeng", "language": "sesotho", "query": "How to start AI gig?"}'
echo "\n"

echo "3️⃣  Testing HRGPT Budget Allocation API..."
curl -X POST http://localhost:3000/api/hireborderless/budget-allocate \
  -H "Content-Type: application/json" \
  -d '{"location": "Sebokeng", "monthly_budget_zar": 5000}'
echo "\n"

echo "🎉 Tests Complete."
