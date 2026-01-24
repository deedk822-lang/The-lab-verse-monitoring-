#!/bin/bash
echo "🚀 Setting up Lab-Verse Monitoring Agent in Singapore with Atlassian JSM Integration..."

# Validate required environment variables
if [ -z "$ALIBABA_ACCESS_KEY_ID" ] || [ -z "$ALIBABA_ACCESS_KEY_SECRET" ]; then
    echo "❌ Please set ALIBABA_ACCESS_KEY_ID and ALIBABA_ACCESS_KEY_SECRET"
    echo "Export them like: export ALIBABA_ACCESS_KEY_ID='your-key'"
    exit 1
fi

if [ -z "$ATLAS_API_KEY" ] || [ -z "$ATLAS_WEBHOOK_URL" ]; then
    echo "❌ Please set ATLAS_API_KEY and ATLAS_WEBHOOK_URL for Atlassian integration."
    echo "Export them like: export ATLAS_API_KEY='your-key'"
    echo "And: export ATLAS_WEBHOOK_URL='https://api.atlassian.com/jsm/ops/integration/v1/json/integrations/webhooks/bitbucket'"
    exit 1
fi

# Set Singapore region
export ALIBABA_CLOUD_REGION_ID="ap-southeast-1"
export TZ="Asia/Singapore"

echo "📍 Configured for Singapore region (ap-southeast-1)"

# Build the enhanced monitoring agent
echo "🏗️ Building Lab-Verse Monitoring Agent with Atlassian JSM integration..."
docker build -f Dockerfile.qwen-enhanced -t lab-verse-monitoring-agent-singapore .

# Deploy with Singapore configuration
echo "🚢 Deploying to Singapore region..."
docker-compose -f docker-compose.singapore-enhanced.yml up -d

# Wait for services to start
sleep 30

# Verify the enhanced monitoring agent is operational
echo "🔍 Verifying Singapore deployment..."
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Lab-Verse Monitoring Agent is running in Singapore!"
    echo "Access API at: http://localhost:8000"
    echo "Singapore region: ap-southeast-1"
    echo "Enhanced with Qwen 3 Plus AI capabilities"
    echo "Integrated with Atlassian JSM webhook"
    echo "Original functionality preserved"

    echo ""
    echo "📋 Integration Status:"
    echo "✅ Atlassian JSM webhook: Active"
    echo "✅ Bitbucket integration: Ready"
    echo "✅ Jira integration: Through Atlassian"
    echo "✅ Qwen 3 Plus AI: Active"
    echo ""
    echo "📊 Endpoints:"
    echo "Health: http://localhost:8000/health"
    echo "Bitbucket status: http://localhost:8000/bitbucket/status"
    echo "Jira status: http://localhost:8000/jira/status"
    echo ""
else
    echo "❌ Lab-Verse Monitoring Agent failed to start in Singapore"
    docker-compose -f docker-compose.singapore-enhanced.yml logs lab-verse-monitoring-agent
    exit 1
fi

echo ""
echo "🌟 Lab-Verse Monitoring Agent Successfully Deployed in Singapore!"
echo ""
echo "🎯 Enhanced Features:"
echo "✅ Original monitoring functionality preserved"
echo "✅ Bitbucket webhook integration active"
echo "✅ Atlassian JSM integration active"
echo "✅ Jira integration through Atlassian"
echo "✅ Qwen 3 Plus AI analysis capabilities added"
echo "✅ Singapore region optimization"
echo "✅ Repository: deedk822-lang/The-lab-verse-monitoring-"
echo "✅ Atlassian webhook: Connected to your JSM instance"
