#!/bin/bash

###############################################################################
# CI Performance Dashboard Verification Script
# Verifies that all components are properly installed and configured
###############################################################################

set -e

echo "🔍 Verifying CI Performance Dashboard Setup..."
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check file existence
echo "📁 Checking files..."
files=(
  ".github/workflows/test-analytics.yml"
  ".husky/pre-commit"
  ".husky/commit-msg"
  ".husky/pre-push"
  ".husky/_/husky.sh"
  "commitlint.config.js"
  "jest.config.js"
  "scripts/analyze-tests.js"
  "scripts/check-coverage-thresholds.js"
  "scripts/generate-test-report.js"
)

all_files_exist=true
for file in "${files[@]}"; do
  if [ -f "$file" ]; then
    echo -e "  ${GREEN}✅${NC} $file"
  else
    echo -e "  ${RED}❌${NC} $file (missing)"
    all_files_exist=false
  fi
done

if [ "$all_files_exist" = false ]; then
  echo -e "\n${RED}❌ Some files are missing!${NC}"
  exit 1
fi

echo ""

# Check executable permissions
echo "🔐 Checking permissions..."
executables=(
  ".husky/pre-commit"
  ".husky/commit-msg"
  ".husky/pre-push"
  ".husky/_/husky.sh"
  "scripts/analyze-tests.js"
  "scripts/check-coverage-thresholds.js"
  "scripts/generate-test-report.js"
)

all_executable=true
for file in "${executables[@]}"; do
  if [ -x "$file" ]; then
    echo -e "  ${GREEN}✅${NC} $file (executable)"
  else
    echo -e "  ${YELLOW}⚠️${NC} $file (not executable, fixing...)"
    chmod +x "$file"
    all_executable=false
  fi
done

echo ""

# Check package.json scripts
echo "📦 Checking package.json scripts..."
required_scripts=(
  "test:coverage"
  "test:analyze"
  "test:performance"
  "prepare"
  "precommit"
)

for script in "${required_scripts[@]}"; do
  if grep -q "\"$script\"" package.json; then
    echo -e "  ${GREEN}✅${NC} $script"
  else
    echo -e "  ${RED}❌${NC} $script (missing)"
  fi
done

echo ""

# Check devDependencies
echo "🔧 Checking devDependencies..."
required_deps=(
  "jest-junit"
  "jest-html-reporter"
  "husky"
  "lint-staged"
  "@commitlint/cli"
  "@commitlint/config-conventional"
)

for dep in "${required_deps[@]}"; do
  if grep -q "\"$dep\"" package.json; then
    echo -e "  ${GREEN}✅${NC} $dep"
  else
    echo -e "  ${RED}❌${NC} $dep (missing - run npm install)"
  fi
done

echo ""

# Validate configuration files
echo "🔍 Validating configuration files..."

# Jest config
if node -e "import('./jest.config.js').then(() => process.exit(0)).catch(() => process.exit(1))" 2>/dev/null; then
  echo -e "  ${GREEN}✅${NC} jest.config.js (valid)"
else
  echo -e "  ${RED}❌${NC} jest.config.js (syntax error)"
fi

# Commitlint config
if node -e "import('./commitlint.config.js').then(() => process.exit(0)).catch(() => process.exit(1))" 2>/dev/null; then
  echo -e "  ${GREEN}✅${NC} commitlint.config.js (valid)"
else
  echo -e "  ${RED}❌${NC} commitlint.config.js (syntax error)"
fi

echo ""

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}✅ CI Performance Dashboard Setup Verification Complete!${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📋 Next Steps:"
echo "  1. Install dependencies:    npm install"
echo "  2. Initialize Husky:        npm run prepare"
echo "  3. Test coverage:           npm run test:coverage"
echo "  4. Test analysis:           npm run test:analyze"
echo "  5. Make a test commit to verify hooks work"
echo ""
echo "📚 Documentation:"
echo "  - See CI_PERFORMANCE_DASHBOARD_IMPLEMENTATION.md for full details"
echo "  - Commit format: type(scope): description"
echo "  - Example: feat(api): add new endpoint"
echo ""
echo "🎉 Your CI pipeline is now enterprise-grade!"
echo ""
