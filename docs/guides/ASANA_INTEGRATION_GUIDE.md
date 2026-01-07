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
- **Scheduled Workflow**: [`.github/workflows/scheduled-asana-cleanup.yml`](https://github.com/deedk822-lang/The-lab-verse-monitoring-/blob/main/.github/workflows/scheduled-asana-cleanup.yml)
- **Analytics Dashboard**: [`.github/workflows/asana-analytics-dashboard.yml`](https://github.com/deedk822-lang/The-lab-verse-monitoring-/blob/main/.github/workflows/asana-analytics-dashboard.yml)

## Basic Usage Guide

### 🎯 Quick Start - Complete All Tasks in a Project

1. **Find Your Project ID** (see [Finding Asana IDs](#finding-asana-ids))
2. **Run the Workflow**:
   - Go to [Actions tab](https://github.com/deedk822-lang/The-lab-verse-monitoring-/actions)
   - Click "Complete Asana Tasks"
   - Click "Run workflow"
   - Select "project_tasks" from the dropdown
   - Enter your Project ID
   - **Recommended**: Test with a single task first
   - Click "Run workflow"

### 📱 All Workflow Options

#### Option 1: Complete Single Task
```
Action Type: single_task
Task ID: [Your task ID]
```

#### Option 2: Complete All Tasks in Project
```
Action Type: project_tasks
Project ID: [Your project ID]
```

#### Option 3: Complete Tasks by Tag
```
Action Type: tagged_tasks
Tag: [Your tag name]
```

#### Option 4: Bulk Complete All Your Tasks (⚠️ Use with Caution)
```
Action Type: bulk_complete
```

## Advanced Features

### 🗓️ Scheduled Automation

**Automatic daily task cleanup** runs at 9 AM UTC (11 AM SAST):

**Available criteria**:
- **overdue**: Complete tasks past their due date
- **ready_tag**: Complete tasks tagged "ready-for-completion"
- **old_completed_subtasks**: Complete parent tasks when all subtasks are done

**Manual scheduling**:
1. Go to Actions → "Scheduled Asana Cleanup"
2. Click "Run workflow"
3. Choose your criteria
4. **Always use dry run first!**

### 🧔 Dry Run Mode

**Test any operation safely without making changes:**

- Shows exactly what would be completed
- No actual task modifications
- Perfect for validation
- Available in all workflows

**Example output:**
```
🔍 WOULD COMPLETE: Design new homepage - Overdue task  
🔍 WOULD COMPLETE: Update documentation - Has ready tag
✅ Would complete: 12 tasks
⏭️  Skipped: 5 tasks
```

### 📈 Analytics Dashboard

**Comprehensive productivity insights:**

- **Completion rates** by project and time period
- **Average time to completion** analysis
- **Trend analysis** with visual charts
- **Project performance** comparisons
- **Exportable reports** (CSV, HTML, JSON)
- **GitHub Pages integration** for live dashboards

**Run analytics manually**:
1. Go to Actions → "Asana Analytics Dashboard"
2. Select analysis period (7, 14, 30, or 90 days)
3. Enable chart generation
4. View results in artifacts and GitHub Pages

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

### 📦 Automatic Backups

**Every operation creates backups:**
- Task information saved before changes
- 30-day artifact retention
- Includes: name, notes, assignee, projects, tags, dates
- Access via Actions → [Workflow Run] → Artifacts

### 🚨 Error Handling & Notifications

**Automated issue creation** for errors:
- Failed workflow runs
- API connectivity problems
- Authentication issues
- Automatic labeling and assignment

**Slack/Teams notifications** (optional):
- Completion summaries
- Error alerts
- Daily/weekly reports

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

**The script shows:**
- All workspaces and projects with IDs
- Recent tasks with IDs
- Available tags
- Direct Asana links

### 🎯 Manual Method: Finding Project ID

1. **Open your project in Asana**
2. **Look at the URL**: `https://app.asana.com/0/PROJECT_ID/list`
3. **Copy the PROJECT_ID number**

**Example**:
- URL: `https://app.asana.com/0/1234567890/list`
- Project ID: `1234567890`

### 🎯 Manual Method: Finding Task ID

1. **Open any task in Asana**
2. **Look at the URL**: `https://app.asana.com/0/PROJECT_ID/TASK_ID`
3. **Copy the TASK_ID number**

**Example**:
- URL: `https://app.asana.com/0/1234567890/9876543210`
- Task ID: `9876543210`

### 🎯 Finding Tag Names

1. **Go to your Asana project**
2. **Look for colored tags on tasks**
3. **Use the exact tag name** (case-insensitive)

## Workflow Options

### Available Workflows

1. **Complete Asana Tasks**: Manual completion with multiple options
2. **Scheduled Asana Cleanup**: Automated daily cleanup
3. **Asana Analytics Dashboard**: Productivity insights and reporting

### Manual Triggers

All workflows support manual execution:

1. Go to [Actions](https://github.com/deedk822-lang/The-lab-verse-monitoring-/actions)
2. Select the desired workflow
3. Click "Run workflow"
4. Configure parameters
5. Execute

### Automatic Triggers

- **Daily Schedule**: Cleanup workflow at 9 AM UTC
- **Weekly Schedule**: Analytics dashboard on Sundays
- **Pull Request Merge**: Automatic task completion
- **Error Events**: Issue creation for failed runs

## Analytics & Monitoring

### 📈 Weekly Analytics Reports

**Automated insights every Sunday:**
- Task completion trends
- Project performance rankings
- Productivity metrics
- Time-to-completion analysis
- Visual charts and graphs

**Access reports:**
- **Live Dashboard**: GitHub Pages integration
- **Artifacts**: Downloadable reports (CSV, JSON, HTML)
- **Summary**: GitHub Actions summary page

### 📊 Key Metrics Tracked

- **Completion Rate**: Percentage of tasks completed
- **Average Completion Time**: Days from creation to completion
- **Project Performance**: Completion rates by project
- **Tag Analysis**: Most frequently used tags
- **Daily Trends**: Completion patterns over time
- **Overdue Analysis**: Tasks past due date

### 🌐 Live Dashboard

**Interactive web dashboard** (updated weekly):
- **URL**: `https://[username].github.io/[repository]/latest/analytics_dashboard.html`
- **Features**: Charts, metrics, insights, trend analysis
- **Mobile responsive** for on-the-go monitoring
- **Exportable data** for custom analysis

## Troubleshooting

### Common Issues

#### ❌ "ASANA_PAT secret not found"
**Solution**: Make sure you've added the `ASANA_PAT` secret to repository settings.

#### ❌ "Task not found" or "Project not found"
**Solutions**:
- Use the ID finder script to verify IDs
- Check Asana permissions for the task/project
- Verify the task/project still exists
- Try refreshing your Asana Personal Access Token

#### ❌ "Permission denied"
**Solutions**:
- Regenerate your Asana Personal Access Token
- Ensure token has necessary workspace permissions
- Update the `ASANA_PAT` secret with new token
- Check Asana workspace member permissions

#### ❌ "No tasks found with tag"
**Solutions**:
- Verify tag name spelling (case-insensitive)
- Check that tagged tasks exist in your workspace
- Ensure you have access to tagged tasks
- Use the ID finder script to list available tags

#### ❌ Workflow runs but no tasks completed
**Solutions**:
- Check if tasks are already completed
- Verify completion criteria settings
- Use dry run mode to see what would be completed
- Review workflow logs for detailed information

### Debug Information

Each workflow provides detailed logging:

1. **Go to Actions** → Select workflow run
2. **Expand job logs** to see step-by-step execution
3. **Check Summary Report** for overview
4. **Download artifacts** for detailed data
5. **Review error messages** for specific solutions

### Performance Optimization

**For large task volumes:**
- Use project-specific completion instead of bulk
- Implement staged completion with tags
- Consider multiple smaller workflows
- Monitor rate limits and adjust timing

## Security Best Practices

### 🔐 Token Management

1. **Regular Rotation**:
   - Rotate Asana PAT every 90 days
   - Update repository secret immediately
   - Test workflows after rotation

2. **Secure Storage**:
   - Always use GitHub Secrets
   - Never commit tokens to repository
   - Avoid storing in workflow files

3. **Access Monitoring**:
   - Monitor token usage in Asana
   - Review API calls regularly
   - Watch for unauthorized access

### 🚫 Access Control

1. **Repository Security**:
   - Limit admin access to trusted team members
   - Use branch protection for workflow files
   - Require code review for workflow changes

2. **Workflow Security**:
   - Monitor all workflow executions
   - Review completion logs regularly
   - Validate before bulk operations

### 📝 Audit Trail

1. **Complete Logging**:
   - All actions logged in GitHub Actions
   - Task backups stored automatically
   - Asana maintains activity history

2. **Monitoring**:
   - Automated error reporting
   - Notification systems for alerts
   - Regular security reviews

## 📞 Support

If you encounter issues:

1. **Check the troubleshooting section** above
2. **Review workflow logs** in GitHub Actions
3. **Use dry run mode** to test safely
4. **Start with single tasks** before bulk operations
5. **Check Asana API status** at [https://status.asana.com/](https://status.asana.com/)

## 🎉 Quick Success Test

To verify everything works:

1. **Create a test task** in Asana
2. **Use the ID finder script** to get the task ID
3. **Run single task workflow** with the ID
4. **Check completion** in Asana
5. **Review workflow logs** for success confirmation
6. **Try other workflow types** as needed

## 💪 Pro Tips

### Productivity Strategies

1. **Smart Tagging**:
   - Tag tasks "ready-for-completion" for batch processing
   - Use priority tags for scheduled automation
   - Create project-specific tags for filtering

2. **Scheduled Automation**:
   - Start with dry run mode for new schedules
   - Use different criteria for different project types
   - Monitor completion patterns with analytics

3. **PR Integration**:
   - Include Asana task IDs in all development PRs
   - Use consistent format for automatic recognition
   - Link related tasks for comprehensive completion

4. **Analytics Usage**:
   - Review weekly reports for productivity insights
   - Identify bottlenecks in task completion
   - Use trends to optimize workflow timing

### Advanced Automation

1. **Custom Criteria**:
   - Combine multiple completion criteria
   - Create project-specific automation rules
   - Implement stage-based completion workflows

2. **Integration Patterns**:
   - Link with CI/CD for deployment completion
   - Connect to project management workflows
   - Integrate with team notification systems

3. **Monitoring & Optimization**:
   - Set up custom dashboards for team metrics
   - Create automated reports for stakeholders
   - Implement continuous improvement processes

---

**🚀 Congratulations!** Your repository now has a comprehensive, production-ready Asana integration system with advanced automation, analytics, and safety features. Start with small tests using dry run mode, then scale up to full automation as your confidence grows.

## 📁 Resource Links

- **Main Integration Guide**: This document
- **ID Finder Utility**: [`scripts/asana-id-finder.py`](https://github.com/deedk822-lang/The-lab-verse-monitoring-/blob/main/scripts/asana-id-finder.py)
- **Primary Workflow**: [`.github/workflows/complete-asana-tasks.yml`](https://github.com/deedk822-lang/The-lab-verse-monitoring-/blob/main/.github/workflows/complete-asana-tasks.yml)
- **Scheduled Cleanup**: [`.github/workflows/scheduled-asana-cleanup.yml`](https://github.com/deedk822-lang/The-lab-verse-monitoring-/blob/main/.github/workflows/scheduled-asana-cleanup.yml)
- **Analytics Dashboard**: [`.github/workflows/asana-analytics-dashboard.yml`](https://github.com/deedk822-lang/The-lab-verse-monitoring-/blob/main/.github/workflows/asana-analytics-dashboard.yml)
- **GitHub Actions**: [Repository Actions](https://github.com/deedk822-lang/The-lab-verse-monitoring-/actions)
- **Asana API Status**: [status.asana.com](https://status.asana.com/)
