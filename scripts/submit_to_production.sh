#!/bin/bash
set -e

echo "🚀 SUBMITTING TO PRODUCTION..."
echo "   - Feature: feat/production-services"
echo "   - Components: Real Security Patrol, Titan Brain, Tax Agent"
echo "   - Target: main branch"

# 1. ENSURE WE ARE ON THE FEATURE BRANCH
# (Just in case you drifted)
git checkout feat/production-services 2>/dev/null || git checkout -b feat/production-services

# 2. FINAL ADD & COMMIT
# Catch any straggling files
git add .
git commit -m "feat: finalize real-time security patrol and empire logic" || echo "Changes already committed."

# 3. SWITCH TO MAIN
echo "🔀 Switching to Main..."
git checkout main

# 4. MERGE THE FEATURE
echo "🔗 Merging Production Services..."
git merge feat/production-services --no-edit

# 5. PUSH TO GITHUB
echo "☁️ Pushing to Origin..."
git push origin main

echo "✅ SUBMISSION COMPLETE."
echo "   - The 'Vaal AI Empire' is now live on the 'main' branch."
echo "   - Next Step: Run 'bash scripts/wake_up_empire.sh' on your Alibaba Cloud Instance."
