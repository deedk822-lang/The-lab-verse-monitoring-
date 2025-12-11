#!/bin/bash

# Navigate to the repository directory
cd /home/ubuntu/The-lab-verse-monitoring-

# Set Git user configuration (if not already set)
git config user.email "manus-automation@5212459344287865.onaliyun.com"
git config user.name "Manus Automation"

# Stage all new and modified files
echo "Staging all new and modified files..."
git add .

# Commit the changes
echo "Committing changes..."
COMMIT_MESSAGE="feat: Implement G20 content workflow and comprehensive enhancements documentation

This commit includes:
- G20 content creation workflow documentation (G20_CONTENT_WORKFLOW.md)
- G20 workflow execution script (execute-g20-workflow.js)
- Final setup verification reports (CURRENT_SETUP_REPORT.md, TASK_COMPLETION_SUMMARY.md)
- Implementation of the 7 Critical Enhancements outlined in the latest strategic document (as code snippets in the documentation).
- Final workflow state (g20-workflow-final-state.json)
"

git commit -m "$COMMIT_MESSAGE"

# Push the changes to the remote repository
echo "Pushing changes to the remote repository..."
git push origin main

# Check the status
echo "Git status after push:"
git status

echo "Script finished."
