#!/bin/bash
set -e

echo "════════════════════════════════════════════════════════════════"
echo "  THE-LAP-VERSE-MONITORING: DEPLOYMENT VERIFICATION"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Check Node.js
echo "✓ Node.js version:"
node --version

# Check npm
echo "✓ npm version:"
npm --version

# Check dependencies
echo ""
echo "✓ Checking dependencies..."
if [ -d "node_modules" ]; then
  echo "  Dependencies installed: $(ls node_modules | wc -l) packages"
else
  echo "  ⚠ Dependencies not installed - run: npm install"
  exit 1
fi

# Check build artifacts
echo ""
echo "✓ Checking build artifacts..."
if [ -d "dist" ]; then
  JS_FILES=$(find dist -name "*.js" | wc -l)
  echo "  Build artifacts: $JS_FILES JavaScript files"
  echo "  Main artifact: $(ls -lh dist/TheLapVerseCore.js | awk '{print $5}')"
else
  echo "  ⚠ Build artifacts not found - run: npm run build"
  exit 1
fi

# Check TypeScript compilation
echo ""
echo "✓ Running TypeScript compilation..."
npm run build > /dev/null 2>&1
if [ $? -eq 0 ]; then
  echo "  Build successful: 0 errors"
else
  echo "  ⚠ Build failed - check TypeScript errors"
  exit 1
fi

# Check key files
echo ""
echo "✓ Checking key files..."
FILES=(
  "src/TheLapVerseCore.ts"
  "src/index.ts"
  "src/resilience/CircuitBreaker.ts"
  "src/middleware/IdempotencyManager.ts"
  "src/cost/FinOpsTagger.ts"
  "src/reliability/SloErrorBudget.ts"
  "src/contracts/OpenApiValidator.ts"
  "src/delivery/OpenFeatureFlags.ts"
  "src/security/SecureLogger.ts"
  "src/kaggle/TheLapVerseKagglePipe.ts"
  "openapi/lapverse.yaml"
  "IMPLEMENTATION.md"
  "QUICKSTART.md"
)

for FILE in "${FILES[@]}"; do
  if [ -f "$FILE" ]; then
    SIZE=$(ls -lh "$FILE" | awk '{print $5}')
    echo "  ✓ $FILE ($SIZE)"
  else
    echo "  ✗ Missing: $FILE"
    exit 1
  fi
done

# Check Redis connectivity (optional)
echo ""
echo "✓ Checking Redis connectivity..."
if command -v redis-cli &> /dev/null; then
  if redis-cli ping > /dev/null 2>&1; then
    echo "  Redis: Connected"
  else
    echo "  ⚠ Redis: Not running - start with: docker run -d -p 6379:6379 redis:7-alpine"
  fi
else
  echo "  ⚠ redis-cli not found - cannot verify Redis"
fi

# Summary
echo ""
echo "════════════════════════════════════════════════════════════════"
echo "  DEPLOYMENT STATUS: READY ✓"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "To start the service:"
echo "  npm run dev          # Development mode"
echo "  npm start            # Production mode"
echo ""
echo "Test endpoints:"
echo "  POST /api/v2/tasks"
echo "  POST /api/v2/self-compete"
echo "  GET  /metrics"
echo ""
echo "Documentation:"
echo "  QUICKSTART.md        60-second setup guide"
echo "  IMPLEMENTATION.md    Full technical documentation"
echo ""
echo "════════════════════════════════════════════════════════════════"
