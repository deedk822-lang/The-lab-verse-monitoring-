#!/bin/bash
# Quick Start Script - Complete Agent Suite
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

set -e

echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║ 🚀 AI Provider Monitoring - Quick Start ║"
echo "╚════════════════════════════════════════════════════════════════════╝"
echo ""

# Check Python version
echo "🔍 Checking Python version..."
python3 --version || { echo "❌ Python 3 not found"; exit 1; }
echo "✅ Python 3 found"
echo ""

# Install dependencies
echo "📦 Installing dependencies..."
pip3 install -q aiohttp prometheus-client requests
echo "✅ Dependencies installed"
echo ""

# Check environment variables
echo "🔐 Checking environment variables..."
if [ -z "$VERCEL_URL" ]; then
export VERCEL_URL="https://the-lab-verse-monitoring.vercel.app/api/research"
echo "⚠️ VERCEL_URL not set, using default: $VERCEL_URL"
else
echo "✅ VERCEL_URL: $VERCEL_URL"
fi

if [ -z "$GRAFANA_CLOUD_PROM_URL" ]; then
echo "⚠️ GRAFANA_CLOUD_PROM_URL not set (metrics won't be pushed)"
else
echo "✅ Grafana Cloud configured"
fi
echo ""

# Menu
echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║ SELECT TEST MODE ║"
echo "╚════════════════════════════════════════════════════════════════════╝"
echo ""
echo "1. 🧪 Quick Test (single request)"
echo "2. 📊 Full Test Suite (8 test cases)"
echo "3. 🔥 Load Test - Burst (10 concurrent)"
echo "4. 📈 Load Test - Ramp Up (5 to 20 concurrent)"
echo "5. ⏱️ Load Test - Sustained (5 concurrent, 60s)"
echo "6. 🔍 Live Monitor (real-time dashboard)"
echo "7. ✅ Validate Grafana Metrics"
echo "8. 🎯 Run Everything (complete validation)"
echo ""
read -p "Enter choice [1-8]: " choice

case $choice in
1)
echo ""
echo "🧪 Running quick test..."
python3 live_test_agent.py "What is AI?"
;;
2)
echo ""
echo "📊 Running full test suite..."
python3 test_suite.py
;;
3)
echo ""
echo "🔥 Running burst load test..."
python3 load_test.py burst 10
;;
4)
echo ""
echo "📈 Running ramp-up load test..."
python3 load_test.py ramp 20 5
;;
5)
echo ""
echo "⏱️ Running sustained load test..."
python3 load_test.py sustained 5 60
;;
6)
echo ""
echo "🔍 Starting live monitor (Ctrl+C to stop)..."
python3 monitor.py 5
;;
7)
echo ""
echo "✅ Validating Grafana metrics..."
python3 validate_metrics.py
;;
8)
echo ""
echo "🎯 Running complete validation suite..."
echo ""

echo "Step 1/4: Quick test..."
python3 live_test_agent.py "Test query" || true
sleep 2

echo ""
echo "Step 2/4: Full test suite..."
python3 test_suite.py 1 || true
sleep 2

echo ""
echo "Step 3/4: Load test..."
python3 load_test.py burst 5 || true
sleep 2

echo ""
echo "Step 4/4: Validate Grafana..."
python3 validate_metrics.py || true

echo ""
echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║ ✅ COMPLETE VALIDATION FINISHED ║"
echo "╚════════════════════════════════════════════════════════════════════╝"
;;
*)
echo "❌ Invalid choice"
exit 1
;;
esac

echo ""
echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║ ✅ COMPLETED ║"
echo "╚════════════════════════════════════════════════════════════════════╝"
echo ""
echo "📊 Check your Grafana dashboard:"
echo " https://dimakatsomoleli.grafana.net"
echo ""
