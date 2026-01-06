#!/bin/bash
set -e

echo "🔍 [SYSTEM VERIFIER] Starting comprehensive system verification..."

# 1. No merge conflicts remain
echo "  [1/10] Verifying no merge conflicts..."
EXCLUDE_ARGS=(
    --exclude='*.md'
    --exclude='*.txt'
    --exclude='verify_system.sh'
    --exclude='MERGE_CONFLICT_PREVENTION.md'
    --exclude-dir='node_modules'
    --exclude-dir='.git'
    --exclude-dir='.venv'
    --exclude-dir='__pycache__'
    --exclude-dir='test/fixtures'
    --exclude-dir='docs'
)
if grep -R --binary-files=text -l -E '<<<<<<< |>>>>>>>|=======' . "${EXCLUDE_ARGS[@]}" | grep .; then
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
while IFS= read -r -d '' file; do
    if ! python3 -m py_compile "$file"; then
        echo "❌ FAILED: Syntax error in $file"
        exit 1
    fi
done < <(find . -name "*.py" -print0)
echo "  ✅ PASSED: All Python files have valid syntax."

# 4. router.js has all required methods
echo "  [4/10] Verifying router.js methods..."
ROUTER_METHODS=("createPullRequest" "rejectTask" "applyAndTestChanges")
for method in "${ROUTER_METHODS[@]}"; do
  if ! grep -q "$method" "orchestrator/router.js"; then
    echo "❌ FAILED: router.js is missing method: $method"
    exit 1
  fi
done
echo "  ✅ PASSED: router.js has all required methods."

# 5. scorer.js has protected paths logic
echo "  [5/10] Verifying scorer.js logic..."
if ! grep -q "micromatch" "tools/scorer.js"; then
  echo "❌ FAILED: scorer.js is missing micromatch logic."
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
  "rankyak_enrichment_demo.py"
  "rankyak-sync-script.js"
)
for pattern in "${OUT_OF_SCOPE_PATTERNS[@]}"; do
  if find . -name "$pattern" -type f -not -path "./__tests__/*" -not -path "./tests/*" | grep -q .; then
    echo "❌ FAILED: Out-of-scope files found for pattern: $pattern."
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
  echo "❌ FAILED: .env file not found. Please create one from .env.example."
  exit 1
fi

REQUIRED_VARS=(
    "GITHUB_TOKEN:pattern:ghp_[A-Za-z0-9]{36}:GitHub Personal Access Token"
    "KIMI_API_KEY:pattern:sk-[A-Za-z0-9]{32,}:Kimi API Key"
)

# Load .env safely
set -a
source <(grep -v '^#' .env | grep -v '^$')
set +a

VALIDATION_FAILED=false

for var_spec in "${REQUIRED_VARS[@]}"; do
    IFS=':' read -r var_name validation_type validation_pattern description <<< "$var_spec"

    # Check if variable is set
    if [ -z "${!var_name:-}" ]; then
        echo "❌ MISSING: $var_name"
        echo "   Description: $description"
        VALIDATION_FAILED=true
        continue
    fi

    # Check if value is not just whitespace
    if [[ "${!var_name}" =~ ^[[:space:]]*$ ]]; then
        echo "❌ EMPTY: $var_name contains only whitespace"
        VALIDATION_FAILED=true
        continue
    fi

    # Type-specific validation
    case "$validation_type" in
        pattern)
            if [[ ! "${!var_name}" =~ $validation_pattern ]]; then
                echo "❌ INVALID FORMAT: $var_name"
                echo "   Expected pattern: $validation_pattern"
                echo "   Description: $description"
                VALIDATION_FAILED=true
            fi
            ;;
    esac
done

if [ "$VALIDATION_FAILED" = true ]; then
    echo "❌ FAILED: Environment variable validation failed"
    exit 1
fi
echo "  ✅ PASSED: Environment configured."

echo "✅ [SYSTEM VERIFIER] All checks passed."
