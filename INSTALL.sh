#!/bin/bash
# Vaal AI Empire - Complete Installation Script
# This script installs EVERYTHING - not just Stripe

set -e  # Exit on error

echo ""
echo "⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡"
echo "   VAAL AI EMPIRE - COMPLETE INSTALLER"
echo "   Digital Sovereignty for SA SMEs"
echo "⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡"
echo ""

# Check Node.js
echo "🔍 Checking Node.js..."
if ! command -v node &> /dev/null; then
    echo "❌ Node.js not installed!"
    echo "Install from: https://nodejs.org/"
    exit 1
fi
echo "✅ Node.js $(node --version)"

# Check npm
if ! command -v npm &> /dev/null; then
    echo "❌ npm not installed!"
    exit 1
fi
echo "✅ npm $(npm --version)"

echo ""
echo "📦 Installing dependencies..."
echo ""

# Install server dependencies
if [ -d "server" ]; then
    echo "🔧 Installing backend (Node.js/Express + Stripe)..."
    cd server
    npm install
    echo "✅ Backend dependencies installed"
    cd ..
else
    echo "⚠️  Server directory not found - skipping backend install"
fi

echo ""
echo "📄 Setting up configuration files..."

# Create .env from example
if [ -f "server/.env.example" ] && [ ! -f "server/.env" ]; then
    cp server/.env.example server/.env
    echo "✅ Created server/.env file"
    echo "⚠️  EDIT server/.env and add your Stripe keys!"
else
    echo "✅ Configuration file already exists"
fi

echo ""
echo "✅✅✅ INSTALLATION COMPLETE! ✅✅✅"
echo ""
echo "🚀 NEXT STEPS:"
echo ""
echo "1. Get Stripe API keys:"
echo "   https://dashboard.stripe.com/test/apikeys"
echo ""
echo "2. Edit server/.env and add:"
echo "   - STRIPE_PUBLISHABLE_KEY=pk_test_..."
echo "   - STRIPE_SECRET_KEY=sk_test_..."
echo ""
echo "3. Create Stripe products:"
echo "   https://dashboard.stripe.com/test/products"
echo "   - Vaal Starter: R999/month"
echo "   - Vaal Empire: R2,999/month"
echo ""
echo "4. Add price IDs to server/.env:"
echo "   - STARTER_PRICE_ID=price_..."
echo "   - EMPIRE_PRICE_ID=price_..."
echo ""
echo "5. Start the server:"
echo "   cd server && npm start"
echo ""
echo "6. Open browser:"
echo "   http://localhost:4242"
echo ""
echo "⚡ Built in the Vaal. Built for Africa. Built to dominate. 🇿🇦"
echo ""