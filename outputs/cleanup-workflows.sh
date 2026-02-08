#!/bin/bash
# CI/CD Pipeline Cleanup Script
# This script safely disables redundant workflows

set -e

echo "🧹 CI/CD Pipeline Cleanup Script"
echo "================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Create backup directory
echo "📁 Creating backup directory..."
mkdir -p .github/workflows.disabled

# Workflows to disable (move to .disabled)
WORKFLOWS_TO_DISABLE=(
    "ci-cd.yml"
    "ci.yml"
    "type-safe-ci.yml"
    "kimi-enhancer.yaml"  # Duplicate of .yml
)

# Workflows to keep but optimize
WORKFLOWS_TO_OPTIMIZE=(
    "llm-code-review.yml"
    "pr-fix-agent.yml"
)

echo ""
echo "🔍 Analyzing current workflows..."
echo ""

# Count total workflows
TOTAL_WORKFLOWS=$(find .github/workflows -name "*.yml" -o -name "*.yaml" | wc -l)
echo "📊 Found $TOTAL_WORKFLOWS workflow files"

# Move redundant workflows
echo ""
echo "🗑️  Disabling redundant workflows..."
for workflow in "${WORKFLOWS_TO_DISABLE[@]}"; do
    if [ -f ".github/workflows/$workflow" ]; then
        echo -e "  ${YELLOW}→${NC} Moving $workflow to .disabled/"
        mv ".github/workflows/$workflow" ".github/workflows.disabled/"
    else
        echo -e "  ${GREEN}✓${NC} $workflow already disabled or not found"
    fi
done

# Add concurrency controls to heavy workflows
echo ""
echo "⚙️  Optimizing heavy workflows..."

# Optimize llm-code-review.yml
if [ -f ".github/workflows/llm-code-review.yml" ]; then
    echo "  → Adding concurrency control to llm-code-review.yml"

    # Check if concurrency already exists
    if ! grep -q "concurrency:" ".github/workflows/llm-code-review.yml"; then
        # Backup original
        cp ".github/workflows/llm-code-review.yml" ".github/workflows.disabled/llm-code-review.yml.backup"

        echo -e "  ${YELLOW}⚠${NC}  Manual optimization needed for llm-code-review.yml"
        echo "      Check .github/workflows.disabled/llm-code-review.yml.backup"
    else
        echo -e "  ${GREEN}✓${NC} llm-code-review.yml already has concurrency control"
    fi
fi

# Optimize pr-fix-agent.yml
if [ -f ".github/workflows/pr-fix-agent.yml" ]; then
    echo "  → Checking pr-fix-agent.yml"

    if ! grep -q "concurrency:" ".github/workflows/pr-fix-agent.yml"; then
        echo -e "  ${YELLOW}⚠${NC}  Manual optimization needed for pr-fix-agent.yml"
    else
        echo -e "  ${GREEN}✓${NC} pr-fix-agent.yml already has concurrency control"
    fi
fi

# Generate summary
echo ""
echo "📊 Cleanup Summary"
echo "=================="
echo ""

REMAINING_WORKFLOWS=$(find .github/workflows -name "*.yml" -o -name "*.yaml" | wc -l)
DISABLED_WORKFLOWS=$(find .github/workflows.disabled -name "*.yml" -o -name "*.yaml" 2>/dev/null | wc -l || echo "0")

echo "  Active workflows: $REMAINING_WORKFLOWS (was $TOTAL_WORKFLOWS)"
echo "  Disabled workflows: $DISABLED_WORKFLOWS"
echo ""

# List remaining workflows
echo "📋 Active Workflows:"
find .github/workflows -name "*.yml" -o -name "*.yaml" | while read file; do
    workflow_name=$(basename "$file")
    echo "  • $workflow_name"
done

echo ""
echo -e "${GREEN}✅ Cleanup complete!${NC}"
echo ""
echo "📝 Next Steps:"
echo "  1. Review the changes: git status"
echo "  2. Test the new pipeline: git add . && git commit -m 'chore: optimize CI/CD'"
echo "  3. Push and watch: git push"
echo "  4. Check PR - should see ~5 checks instead of 12"
echo ""
echo "📖 For details, see: PIPELINE_MIGRATION_GUIDE.md"
echo ""

# Create a git status summary
echo "🔍 Git Status:"
echo ""
git status --short .github/workflows* 2>/dev/null || echo "  (Run git status to see changes)"

echo ""
echo "💡 Tip: The new main-ci.yml consolidates all essential checks"
echo "         into a single, efficient pipeline with proper dependencies."
echo ""
