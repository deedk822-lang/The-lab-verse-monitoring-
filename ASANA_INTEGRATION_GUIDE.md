# 🚀 Complete Asana-GitHub Integration Guide

This guide will help you set up and use the comprehensive Asana task completion system in your GitHub repository.

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Initial Setup](#initial-setup)
3. [Basic Usage Guide](#basic-usage-guide)
4. [Advanced Features](#advanced-features)
5. [Finding Asana IDs](#finding-asana-ids)
6. [Workflow Options](#workflow-options)
7. [Analytics & Monitoring](#analytics--monitoring)
8. [Troubleshooting](#troubleshooting)
9. [Security Best Practices](#security-best-practices)

## Prerequisites

- Admin access to your Asana workspace
- Admin access to this GitHub repository
- An active Asana account with projects and tasks
- (Optional) Slack/Teams webhook for notifications

## Initial Setup

### Step 1: Generate Asana Personal Access Token

1. **Go to Asana Developer Console**
   - Visit: [https://app.asana.com/0/my-apps](https://app.asana.com/0/my-apps)
   - Click "Manage Developer Apps"

2. **Create New Personal Access Token**
   - Click "New personal access token"
   - Name it: `GitHub Actions Integration`
   - Click "Create token"
   - **⚠️ IMPORTANT**: Copy the token immediately - you won't see it again!

### Step 2: Add Token to GitHub Repository Secrets

1. **Navigate to Repository Settings**
   - Go to your repository: [The-lab-verse-monitoring-](https://github.com/deedk822-lang/The-lab-verse-monitoring-)
   - Click "Settings" tab
   - Go to "Secrets and variables" → "Actions"

2. **Create Repository Secret**
   - Click "New repository secret"
   - Name: `ASANA_PAT`
   - Value: [Paste your Asana token here]
   - Click "Add secret"

### Step 3: Optional Notification Setup

**For Slack notifications** (optional):
- Add `SLACK_WEBHOOK_URL` secret with your Slack webhook URL

**For Teams notifications** (optional):
- Add `TEAMS_WEBHOOK_URL` secret with your Teams webhook URL

### Step 4: Verify Workflow Installation

✅ The workflow files have been created in your repository:

- **Main Workflow**: [`.github/workflows/complete-asana-tasks.yml`](https://github.com/deedk822-lang/The-lab-verse-monitoring-/blob/main/.github/workflows/complete-asana-tasks.yml)
- **Scheduled Workflow**: [`.github/workflows/scheduled-asana-completion.yml`](https://github.com/deedk822-lang/The-lab-verse-monitoring-/blob/main/.github/workflows/scheduled-asana-completion.yml)

## Basic Usage Guide

### 🎯 Quick Start - Complete All Tasks in a Project

1. **Find Your Project ID** (see [Finding Asana IDs](#finding-asana-ids))
2. **Run the Workflow**:
   - Go to [Actions tab](https://github.com/deedk822-lang/The-lab-verse-monitoring-/actions)
   - Click "Complete Asana Tasks"
   - Click "Run workflow"
   - Select "project_tasks" from the dropdown
   - Enter your Project ID
   - **Recommended**: Set "Dry Run" to "true" for first test
   - Click "Run workflow"

### 📱 All Workflow Options

#### Option 1: Complete Single Task
```
Action Type: single_task
Task ID: [Your task ID]
Dry Run: false (or true for testing)
Check Dependencies: false (or true for safety)
```

#### Option 2: Complete All Tasks in Project
```
Action Type: project_tasks
Project ID: [Your project ID]
Dry Run: false (or true for testing)
```

#### Option 3: Complete Tasks by Tag
```
Action Type: tagged_tasks
Tag: [Your tag name]
Dry Run: false (or true for testing)
```

#### Option 4: Bulk Complete All Your Tasks (⚠️ Use with Extreme Caution)
```
Action Type: bulk_complete
Dry Run: true (HIGHLY recommended for first run)
```

## Advanced Features

### 🧪 Dry Run Mode

**Always test first with dry run mode!**

- Set "Dry Run" to "true" in any workflow
- Shows exactly what would be completed without actually completing tasks
- Perfect for validation and testing
- No risk of accidentally completing wrong tasks

**Example dry run output:**
```
🧪 WOULD COMPLETE: Design new login page - Overdue task
🧪 WOULD COMPLETE: Update API documentation - Tagged as ready for completion
✅ Would complete: 15 tasks
⏭️ Skipped: 3 tasks
```

### ⏰ Scheduled Automation

**Automatic daily completion** at 9 AM UTC:

1. **Configure criteria** in the scheduled workflow
2. **Available criteria**:
   - `overdue_tasks`: Complete overdue tasks
   - `tagged_ready`: Complete tasks tagged as "ready-for-completion"
   - `low_priority`: Complete old, low-priority tasks
   - `old_completed_projects`: Complete tasks in finished projects

3. **Run manually for testing**:
   - Go to Actions → "Scheduled Asana Completion"
   - Set "Dry Run" to "true"
   - Choose your criteria
   - Test before enabling automatic runs

### 🔗 Task Dependencies

**Prevent completing tasks with incomplete dependencies:**

- Enable "Check Dependencies" in any workflow
- System automatically skips tasks with incomplete prerequisites
- Ensures logical task completion order
- Prevents breaking project workflows

### 💾 Automatic Backups

**Every completed task is automatically backed up:**

- Task information saved before completion
- Includes: name, notes, assignee, projects, tags, dates
- Stored as artifacts in workflow runs
- 30-day retention for recovery
- Access via Actions → [Workflow Run] → Artifacts

### 🔄 Automatic PR Integration

**Tasks completed automatically when PRs are merged:**

**Supported formats in PR description:**
```markdown
## Asana Task
asana-task-id: 1234567890

## Or
Task ID: 1234567890

## Or direct URL
https://app.asana.com/0/project_id/task_id
```

## Finding Asana IDs

### 🎯 Easy Method: Use the ID Finder Script

**Run locally to find all your IDs:**

```bash
# Install dependencies
pip install -r scripts/requirements.txt

# Set your token
export ASANA_PAT="your_personal_access_token"

# Run the finder
python scripts/asana-id-finder.py
```

**The script will show:**
- All your workspaces and projects with IDs
- Recent tasks with IDs
- Available tags
- Direct links to everything

### 🎯 Manual Method: Finding Project ID

1. **Open your project in Asana**
2. **Look at the URL**: `https://app.asana.com/0/PROJECT_ID/list`
3. **Copy the PROJECT_ID number**

### 🎯 Manual Method: Finding Task ID

1. **Open any task in Asana**
2. **Look at the URL**: `https://app.asana.com/0/PROJECT_ID/TASK_ID`
3. **Copy the TASK_ID number**

## Workflow Options

### Manual Triggers

**Two main workflows available:**

1. **Complete Asana Tasks**: Manual/PR-triggered completion
2. **Scheduled Asana Completion**: Automated daily completion

**Both support:**
- Dry run mode for testing
- Multiple completion criteria
- Comprehensive reporting
- Backup creation

### Automatic Triggers

- **Daily Schedule**: 9 AM UTC (customizable)
- **Pull Request Merge**: Automatic task completion
- **Manual Override**: Run anytime via Actions tab

## Analytics & Monitoring

### 📊 Analytics Dashboard

**Comprehensive productivity analytics:**

```bash
# Install dependencies
pip install -r scripts/requirements.txt

# Set your token
export ASANA_PAT="your_personal_access_token"

# Run analytics for last 30 days
python scripts/asana-analytics-dashboard.py --days 30

# Export as HTML report
python scripts/asana-analytics-dashboard.py --days 30 --export html

# Analyze specific project
python scripts/asana-analytics-dashboard.py --project PROJECT_ID --trend-analysis
```

**Analytics include:**
- **Completion rates** by project and time period
- **Productivity score** (0-100)
- **Time analysis**: average completion times
- **Trend analysis**: velocity and predictions
- **Recommendations**: personalized improvement suggestions

### 📈 Real-time Monitoring

**Each workflow run provides:**

- **Detailed completion logs**
- **Summary reports** with metrics
- **Error handling** with specific solutions
- **Artifact storage** for backups and reports
- **Notification integration** (Slack/Teams)

### 🚨 Automated Alerts

**System automatically creates GitHub issues for:**
- Failed workflow runs
- API connectivity issues
- Authentication problems
- Unexpected errors

## Troubleshooting

### Common Issues

#### ❌ "ASANA_PAT secret not found"
**Solution**: Add the `ASANA_PAT` secret to repository settings.

#### ❌ "Task not found" or "Project not found"
**Solutions**:
- Use the ID finder script to verify IDs
- Check access permissions in Asana
- Ensure task/project still exists

#### ❌ "Task has incomplete dependencies"
**This is normal when dependency checking is enabled**
- Review task dependencies in Asana
- Complete prerequisite tasks first
- Or disable dependency checking

#### ❌ Workflow runs but nothing happens
**Solutions**:
- Check if tasks are already completed
- Verify completion criteria
- Use dry run mode to debug
- Check workflow logs for details

### Debug Steps

1. **Always start with dry run mode**
2. **Check workflow logs** in Actions tab
3. **Use the ID finder script** to verify IDs
4. **Test with a single task** before bulk operations
5. **Review the summary reports** for insights

## Security Best Practices

### 🔐 Token Management
- **Rotate tokens** every 90 days
- **Use repository secrets** only
- **Never commit tokens** to code
- **Monitor token usage** in Asana

### 🛡️ Access Control
- **Limit repository access** to trusted team members
- **Use branch protection** for workflow files
- **Monitor workflow runs** regularly
- **Review completion logs** for accuracy

### 📋 Audit Trail
- **All actions logged** in GitHub Actions
- **Task backups** stored automatically
- **Asana activity log** tracks changes
- **Notification systems** for real-time alerts

## 🎉 Quick Success Test

**Verify everything works:**

1. **Create a test task** in Asana
2. **Run ID finder script** to get the task ID
3. **Run workflow in dry run mode** first
4. **Review the dry run results**
5. **Run again with dry run = false**
6. **Check task completion** in Asana
7. **Review workflow logs** and summary

## 💡 Pro Tips

### Best Practices
- **Always use dry run first** for new operations
- **Start small** with single tasks before bulk operations
- **Use dependency checking** for complex projects
- **Regular analytics review** to optimize productivity
- **Tag tasks strategically** for automated completion

### Productivity Strategies
- **Tag tasks "ready-for-completion"** for batch processing
- **Use scheduled completion** for routine tasks
- **Implement PR-based completion** for development workflows
- **Monitor analytics weekly** for trend insights
- **Set up notifications** for team coordination

### Advanced Automation
- **Create completion rules** based on project phases
- **Use multiple tags** for different completion criteria
- **Integrate with CI/CD** for deployment-triggered completion
- **Set up custom schedules** for different project types

---

**🚀 You're all set!** Your GitHub repository now has a production-ready, feature-rich Asana task completion system with analytics, automation, and safety features. Start with dry runs and small tests, then scale up to full automation as needed.

## 📞 Support & Resources

- **Integration Guide**: This document
- **ID Finder**: `scripts/asana-id-finder.py`
- **Analytics Dashboard**: `scripts/asana-analytics-dashboard.py`
- **Main Workflow**: `.github/workflows/complete-asana-tasks.yml`
- **Scheduled Workflow**: `.github/workflows/scheduled-asana-completion.yml`
- **GitHub Actions**: [Repository Actions](https://github.com/deedk822-lang/The-lab-verse-monitoring-/actions)
- **Asana API Status**: [status.asana.com](https://status.asana.com/)
