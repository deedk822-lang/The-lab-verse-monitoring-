#!/bin/bash
# Deploy with OpenTelemetry configuration

echo "🚀 Deploying AI Provider Monitoring with OpenTelemetry"
echo ""

# Check if credentials are set
if [ -z "$GRAFANA_INSTANCE_ID" ] || [ -z "$GRAFANA_API_TOKEN" ]; then
    echo "❌ Error: GRAFANA_INSTANCE_ID and GRAFANA_API_TOKEN must be set"
    echo ""
    echo "Set them with:"
    echo "  export GRAFANA_INSTANCE_ID=your_instance_id"
    echo "  export GRAFANA_API_TOKEN=your_api_token"
    exit 1
fi

# Generate Base64 credentials
CREDENTIALS=$(echo -n "${GRAFANA_INSTANCE_ID}:${GRAFANA_API_TOKEN}" | base64)
echo "✅ Generated Base64 credentials"

# Install OpenTelemetry dependencies
echo "📦 Installing OpenTelemetry dependencies..."
npm install --save \
  @opentelemetry/sdk-node \
  @opentelemetry/exporter-trace-otlp-http \
  @opentelemetry/exporter-metrics-otlp-http \
  @opentelemetry/sdk-metrics \
  @opentelemetry/resources \
  @opentelemetry/semantic-conventions \
  @opentelemetry/api

echo "✅ Dependencies installed"

# Set Vercel environment variables
echo "🔧 Setting Vercel environment variables..."

vercel env add OTEL_EXPORTER_OTLP_ENDPOINT production <<< "https://otlp-gateway-prod-us-central-0.grafana.net/otlp"
vercel env add OTEL_EXPORTER_OTLP_PROTOCOL production <<< "http/protobuf"
vercel env add OTEL_EXPORTER_OTLP_HEADERS production <<< "Authorization=Basic ${CREDENTIALS}"
vercel env add OTEL_SERVICE_NAME production <<< "ai-provider-monitoring"
vercel env add OTEL_RESOURCE_ATTRIBUTES production <<< "service.name=ai-provider-monitoring,deployment.environment=production"

echo "✅ Environment variables set"

# Commit and push
echo "📝 Committing changes..."
git add .
git commit -m "feat: add OpenTelemetry instrumentation for Grafana Cloud"
git push

echo ""
echo "✅ Deployment complete!"
echo ""
echo "Next steps:"
echo "1. Wait for Vercel deployment to complete"
echo "2. Make a test request to generate traces"
echo "3. Check Grafana Cloud for data (wait 30-60 seconds)"
echo ""
echo "Test with:"
echo "  curl -X POST https://the-lab-verse-monitoring.vercel.app/api/research \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"q\":\"Test OpenTelemetry\"}'"
