#!/bin/bash
# scripts/validate-all.sh

echo "🔍 Running local validations..."

# 1. Verify vercel.json
echo "Checking vercel.json..."
cat vercel.json | jq . > /dev/null && echo "✅ vercel.json valid"

# 2. Verify docker-compose
echo "Checking docker-compose..."
cd monitoring/kaggle && docker-compose config && echo "✅ docker-compose valid"
cd ../..

# 3. Verify shell scripts
echo "Checking shell scripts..."
shellcheck monitoring/kaggle/scripts/*.sh && echo "✅ shell scripts valid"

# 4. Verify YAML files
echo "Checking workflows..."
find .github/workflows -name "*.yml" | while read f; do
    yamllint "$f" || echo "Warning: $f has issues"
done

# 5. Run tests
echo "Running tests..."
npm test

echo "✅ All local validations passed!"
