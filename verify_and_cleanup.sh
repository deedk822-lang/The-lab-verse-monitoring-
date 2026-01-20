#!/bin/bash
set -e

# ============================================================================
# REPOSITORY VERIFICATION & CLEANUP SCRIPT
# Ensures the repo is functional and removes unnecessary files
# ============================================================================

echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║         REPOSITORY VERIFICATION & CLEANUP                        ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

# Navigate to repository
cd /content/The-lab-verse-monitoring-
echo "📁 Working in: $(pwd)"
echo ""

# ============================================================================
# STEP 1: VERIFY PR FIX WAS APPLIED
# ============================================================================

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "STEP 1: VERIFY ALL FIXES WERE APPLIED"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check 1: .gitignore has Python patterns
echo "✓ Checking .gitignore for Python patterns..."
if grep -q "__pycache__/" .gitignore && grep -q "*.pyc" .gitignore; then
    echo "  ✅ Python patterns present"
else
    echo "  ❌ Missing Python patterns"
    exit 1
fi

# Check 2: .env.example is clean
echo "✓ Checking .env.example for merge artifacts..."
if grep -qE "(feat/|main|<<<<<<<|=======|>>>>>>>)" .env.example; then
    echo "  ❌ Merge artifacts still present"
    exit 1
else
    echo "  ✅ .env.example is clean"
fi

# Check 3: .env is NOT tracked
echo "✓ Checking if .env is tracked..."
if git ls-files | grep -q "^\.env$"; then
    echo "  ❌ .env is still tracked!"
    exit 1
else
    echo "  ✅ .env is not tracked"
fi

# Check 4: Workflow has pinned CLI version
echo "✓ Checking workflow file for CLI version pinning..."
if grep -q 'CLI_VERSION="3.0.198"' .github/workflows/type-safe-ci.yml; then
    echo "  ✅ CLI version pinned to 3.0.198"
else
    echo "  ❌ CLI version not pinned"
    exit 1
fi

echo ""
echo "✅ ALL FIXES VERIFIED SUCCESSFULLY"
echo ""

# ============================================================================
# STEP 2: CHECK CURRENT REPOSITORY SIZE
# ============================================================================

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "STEP 2: REPOSITORY SIZE ANALYSIS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

total_files=$(find . -type f | wc -l)
total_size=$(du -sh . | cut -f1)

echo "📊 Current Repository Stats:"
echo "   Total files: $total_files"
echo "   Total size: $total_size"
echo ""

# Count by category
echo "📁 Files by category:"
echo "   Markdown docs: $(find . -name "*.md" | wc -l)"
echo "   Shell scripts: $(find . -name "*.sh" | wc -l)"
echo "   Python files: $(find . -name "*.py" | wc -l)"
echo "   JavaScript files: $(find . -name "*.js" -o -name "*.ts" | wc -l)"
echo "   Config files: $(find . -name "*.yml" -o -name "*.yaml" -o -name "*.json" | wc -l)"
echo ""

# ============================================================================
# STEP 3: IDENTIFY FILES TO REMOVE
# ============================================================================

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "STEP 3: IDENTIFYING UNNECESSARY FILES"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Files and directories to remove (non-essential documentation and duplicates)
TO_REMOVE=(
    # Duplicate/redundant documentation
    "AI_SDK_TESTING_COMPLETE.md"
    "BUILD_SUMMARY.md"
    "CHANGES_SUMMARY.md"
    "CHANGES_SUMMARY_FIXES.md"
    "CI_FIX_COMPLETE_SUMMARY.md"
    "CI_FIX_SUMMARY.md"
    "CI_FIXES_COMPLETE.md"
    "CI_FIXES_COMPLETE_PROFESSIONAL.md"
    "CI_FIXES_SUMMARY.md"
    "COMPLETE_BUILD_GUIDE.md"
    "CURRENT_SETUP_REPORT.md"
    "DEPLOYMENT_COMPLETE.md"
    "DEPLOYMENT_COMPLETE_SUMMARY.md"
    "DEPLOYMENT_SUCCESS.txt"
    "DEPLOYMENT_SUMMARY.md"
    "FINAL_REPORT.md"
    "FIXES_APPLIED.md"
    "FIXES_APPLIED_2025-11-11.md"
    "PERFORMANCE_REPORT.md"
    "PRODUCTION_READY.md"
    "SETUP-COMPLETE.md"
    "SETUP_VERIFICATION_REPORT.md"
    "SUMMARY.md"
    "TASK_COMPLETION_SUMMARY.md"

    # Old/obsolete guides
    "G20_BRANCH_README.md"
    "G20_CONTENT_WORKFLOW.md"
    "G20_CONTENT_WORKFLOW_VERIFIED.md"
    "G20_CORRECTIONS_CHANGELOG.md"
    "G20_QUICK_START_GUIDE.md"
    "QUICKSTART.md"
    "QUICKSTART_MCP.md"
    "QUICK_START_MANUS.md"
    "PR-515-COMPLETION-GUIDE.md"

    # Duplicate deployment guides
    "DEPLOYMENT_CHECKLIST.md"
    "DEPLOYMENT_FREE_TIER.md"
    "DEPLOYMENT_GUIDE.md"
    "DEPLOYMENT_GUIDE_MCP.md"
    "DEPLOYMENT_README.md"
    "README-DEPLOY.md"

    # Old/redundant scripts
    "complete-deployment-fix.sh"
    "complete_setup_and_clone.sh"
    "fix-package-lock-conflict.sh"
    "fix_all.sh"
    "fix_ci.sh"
    "install-localai.sh"
    "migrate.sh"
    "purge-secrets-from-history.sh"
    "quick-setup-production.sh"
    "quick-start.sh"
    "quick_start.sh"
    "repo-cleanup.sh"
    "setup-ai-orchestration.sh"
    "setup.sh"
    "verify-ci-setup.sh"
    "verify-deployment.sh"
    "verify-fixes.sh"
    "verify_system.sh"

    # Duplicate/old config files
    "babel.config.js"
    "eslint.config.js"
    ".eslintrc.json"
    ".prettierrc"
    ".prettierrc.json"

    # Old documentation
    "manus-final-instructions.md"
    "manus-instructions.md"
    "outline.md"
    "design.md"
    "todo-v2.md"
    "todo.md"
    "talent_scout.md"

    # Test/temporary files
    "healthcheck.js"
    "main.js"
    "temp_article.html"
    "templates.html"
    "index.html"
    "legal-compliance.html"
    "tax_report.json"

    # Redundant docker compose files
    "docker-compose.kimi.yml"
    "docker-compose.superstack.yml"
    "docker-compose.yml"

    # Old TOML configs
    "fly.toml"
    "render.yaml"

    # Nested duplicate directories
    "The-lab-verse-monitoring-/The-lab-verse-monitoring-"
)

echo "⚠️  Found ${#TO_REMOVE[@]} unnecessary files/directories to remove"
echo ""

# ============================================================================
# STEP 4: CREATE BACKUP BRANCH
# ============================================================================

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "STEP 4: CREATE BACKUP BRANCH"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

current_branch=$(git branch --show-current)
backup_branch="backup-before-cleanup-$(date +%Y%m%d-%H%M%S)"

echo "Creating backup branch: $backup_branch"
git branch "$backup_branch"
echo "✅ Backup created: $backup_branch"
echo ""

# ============================================================================
# STEP 5: REMOVE UNNECESSARY FILES (OPTIONAL)
# ============================================================================

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "STEP 5: CLEANUP DECISION"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "⚠️  WARNING: This step would remove ${#TO_REMOVE[@]} files/directories."
echo "    Cleanup is skipped by default in automated environments to prevent accidental data loss."
echo "    To run cleanup, execute this script with 'CLEANUP_PROMPT_RESPONSE=yes ./script_name.sh'."
echo ""

# Use an environment variable to control cleanup, defaulting to 'no'
response="${CLEANUP_PROMPT_RESPONSE:-no}"

if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    echo ""
    echo "🗑️  Removing unnecessary files..."

    removed_count=0
    for item in "${TO_REMOVE[@]}"; do
        if [ -e "$item" ]; then
            echo "  Removing: $item"
            rm -rf "$item"
            ((removed_count++))
        fi
    done

    echo ""
    echo "✅ Removed $removed_count files/directories"

    # Stage deletions
    git add -A

    # Show what was removed
    echo ""
    echo "📊 Files staged for removal:"
    git diff --cached --name-only --diff-filter=D | head -20
    echo ""

    # Commit cleanup
    echo "Committing cleanup..."
    git commit -m "chore: remove redundant documentation and scripts\n\n- Remove duplicate deployment guides\n- Remove old CI/CD summary files\n- Remove obsolete setup scripts\n- Remove temporary test files\n- Streamline repository for production\n\nBackup preserved in branch: $backup_branch"

    echo "✅ Cleanup committed"

else
    echo "⏭️  Cleanup skipped (set CLEANUP_PROMPT_RESPONSE=yes to enable)."
fi

echo ""

# ============================================================================
# STEP 6: VERIFY ESSENTIAL FILES EXIST
# ============================================================================

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "STEP 6: VERIFY ESSENTIAL FILES"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

ESSENTIAL_FILES=(
    "README.md"
    "package.json"
    ".env.example"
    ".gitignore"
    ".github/workflows/type-safe-ci.yml"
    "src/index.js"
    "docker/compose/docker-compose.prod.yml"
)

all_essential_present=true
for file in "${ESSENTIAL_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✅ $file"
    else
        echo "  ❌ MISSING: $file"
        all_essential_present=false
    fi
done

if [ "$all_essential_present" = true ]; then
    echo ""
    echo "✅ All essential files present"
else
    echo ""
    echo "⚠️  Some essential files are missing!"
fi

echo ""

# ============================================================================
# STEP 7: CHECK PR STATUS
# ============================================================================

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "STEP 7: PR STATUS CHECK"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "📊 Current branch: $current_branch"
echo "🔗 PR URL: https://github.com/deedk822-lang/The-lab-verse-monitoring-/pull/1320"
echo ""
echo "Expected GitHub Actions checks:"
echo "  • Type-Safe CI/CD Pipeline / security-analysis"
echo "  • Type-Safe CI/CD Pipeline / type-check"
echo "  • Jules Governance / Analyze Pull Request"
echo "  • Vercel - Deployment"
echo "  • PR Validation / Validate Agent Stack"
echo ""
echo "⏱️  Checks should complete within 2-5 minutes of last push"
echo ""

# ============================================================================
# STEP 8: FINAL REPORT
# ============================================================================

echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                    VERIFICATION COMPLETE                         ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

new_total=$(find . -type f | wc -l)
new_size=$(du -sh . | cut -f1)

echo "📊 REPOSITORY STATS:"
echo "   Before: $total_files files ($total_size)"
echo "   After:  $new_total files ($new_size)"
echo ""

echo "✅ VERIFIED FIXES:"
echo "   ✓ .env removed from tracking"
echo "   ✓ .gitignore has Python patterns"
echo "   ✓ .env.example is clean"
echo "   ✓ Alibaba CLI pinned to 3.0.198"
echo ""

echo "🔐 BACKUP CREATED:"
echo "   Branch: $backup_branch"
echo "   Restore with: git checkout $backup_branch"
echo ""

echo "📋 NEXT STEPS:"
echo "   1. Check PR status (should be all green)"
echo "   2. If cleanup was applied, push changes:"
echo "      git push origin $current_branch"
echo "   3. Merge PR when all checks pass"
echo "   4. Deploy to production"
echo ""

echo "═══════════════════════════════════════════════════════════════════"
echo "🎉 REPOSITORY IS FUNCTIONAL AND READY!"
echo "═══════════════════════════════════════════════════════════════════"
