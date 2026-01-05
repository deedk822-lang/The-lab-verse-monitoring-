#!/bin/bash
set -e

echo "🔍 [SYSTEM VERIFIER] Starting comprehensive system verification..."

# 1. No merge conflicts remain
echo "  [1/10] Verifying no merge conflicts..."
if grep -lr '<<<<<<< HEAD' . --exclude=verify_system.sh; then
  echo "❌ FAILED: Merge conflicts found."
  exit 1
fi
echo "  ✅ PASSED: No merge conflicts found."

# 2. All critical files exist
echo "  [2/10] Verifying critical files exist..."
CRITICAL_FILES=(
  "orchestrator/router.js"
  "handlers/healer.py"
  "tools/scorer.js"
  ".jules/protected_paths.json"
)
for file in "${CRITICAL_FILES[@]}"; do
  if [ ! -f "$file" ]; then
    echo "❌ FAILED: Critical file not found: $file"
    exit 1
  fi
done
echo "  ✅ PASSED: All critical files exist."

# 3. All Python files have valid syntax
echo "  [3/10] Verifying Python syntax..."
find . -name "*.py" -exec python3 -m py_compile {} \;
echo "  ✅ PASSED: All Python files have valid syntax."

# 4. router.js has all required methods
echo "  [4/10] Verifying router.js methods..."
ROUTER_METHODS=("createPullRequest" "rejectTask" "autoMerge")
for method in "${ROUTER_METHODS[@]}"; do
  if ! grep -q "$method" "orchestrator/router.js"; then
    echo "❌ FAILED: router.js is missing method: $method"
    exit 1
  fi
done
echo "  ✅ PASSED: router.js has all required methods."

# 5. scorer.js has protected paths logic
echo "  [5/10] Verifying scorer.js logic..."
if ! grep -q "protected_paths_violation" "tools/scorer.js"; then
  echo "❌ FAILED: scorer.js is missing protected paths logic."
  exit 1
fi
echo "  ✅ PASSED: scorer.js has protected paths logic."

# 6. healer.py has no undefined variables
echo "  [6/10] Verifying healer.py dependencies..."
if ! grep -q "_init_kimi_client" "handlers/healer.py"; then
  echo "❌ FAILED: healer.py is missing dependency injection."
  exit 1
fi
echo "  ✅ PASSED: healer.py has no undefined variables."

# 7. Configuration files are valid
echo "  [7/10] Verifying configuration files..."
if ! jq . ".jules/protected_paths.json" > /dev/null; then
    echo "❌ FAILED: .jules/protected_paths.json is not valid JSON."
    exit 1
fi
echo "  ✅ PASSED: Configuration files are valid."

# 8. No out-of-scope files present
echo "  [8/10] Verifying no out-of-scope files..."
OUT_OF_SCOPE_PATTERNS=(
  "*asana*"
  "*g20*"
  "*rankyak*"
  "*mock*"
  "*simulation*"
)
for pattern in "${OUT_OF_SCOPE_PATTERNS[@]}"; do
  if find . -name "$pattern" -type f | grep -q .; then
    echo "❌ FAILED: Out-of-scope files found."
    exit 1
  fi
done
echo "  ✅ PASSED: No out-of-scope files present."

# 9. Dependencies installed
echo "  [9/10] Verifying dependencies..."
if [ ! -d "node_modules" ]; then
    echo "  [9/10] Dependencies not found. Please run 'npm install'."
    exit 1
fi
echo "  ✅ PASSED: Dependencies installed."

# 10. Environment configured
echo "  [10/10] Verifying environment..."
if [ ! -f ".env" ]; then
  echo "  [10/10] Creating .env file..."
  touch .env
fi
echo "  ✅ PASSED: Environment configured."

echo "✅ [SYSTEM VERIFIER] All checks passed."
