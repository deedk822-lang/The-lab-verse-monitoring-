# 🚀 Complete Asana-GitHub Integration Guide

This guide will help you set up and use the comprehensive Asana task completion system in your GitHub repository.

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Initial Setup](#initial-setup)
3. [Usage Guide](#usage-guide)
4. [Finding Asana IDs](#finding-asana-ids)
5. [Workflow Options](#workflow-options)
6. [Troubleshooting](#troubleshooting)
7. [Advanced Features](#advanced-features)

## Prerequisites

- Admin access to your Asana workspace
- Admin access to this GitHub repository
- An active Asana account with projects and tasks

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

### Step 3: Verify Workflow Installation

✅ The workflow file `complete-asana-tasks.yml` has already been created in your repository!

You can find it at: [`.github/workflows/complete-asana-tasks.yml`](https://github.com/deedk822-lang/The-lab-verse-monitoring-/blob/main/.github/workflows/complete-asana-tasks.yml)

## Usage Guide

### 🎯 Quick Start - Complete All Tasks in a Project

This is the fastest way to complete all tasks in a specific project:

1. **Find Your Project ID** (see [Finding Asana IDs](#finding-asana-ids))
2. **Run the Workflow**:
   - Go to [Actions tab](https://github.com/deedk822-lang/The-lab-verse-monitoring-/actions)
   - Click "Complete Asana Tasks"
   - Click "Run workflow"
   - Select "project_tasks" from the dropdown
   - Enter your Project ID
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

### 🔄 Automatic Completion from Pull Requests

The workflow automatically detects and completes tasks when you merge pull requests that contain Asana task references.

**Supported formats in PR description:**
- `asana-task-id: 1234567890`
- `Task ID: 1234567890`
- Full Asana URL: `https://app.asana.com/0/project_id/task_id`

## Finding Asana IDs

### 🎯 Finding Project ID

1. **Open your project in Asana**
2. **Look at the URL**: `https://app.asana.com/0/PROJECT_ID/list`
3. **Copy the PROJECT_ID number**

**Example**:
- URL: `https://app.asana.com/0/1234567890/list`
- Project ID: `1234567890`

### 🎯 Finding Task ID

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

### Manual Triggers

All workflows can be triggered manually from the GitHub Actions interface:

1. Go to [Actions](https://github.com/deedk822-lang/The-lab-verse-monitoring-/actions)
2. Select "Complete Asana Tasks"
3. Click "Run workflow"
4. Fill in the required parameters
5. Click "Run workflow"

### Automatic Triggers

- **Pull Request Merge**: Automatically completes tasks referenced in PR descriptions
- **Webhook Integration**: Can be extended for external triggers

## Troubleshooting

### Common Issues

#### ❌ "ASANA_PAT secret not found"
**Solution**: Make sure you've added the `ASANA_PAT` secret to your repository settings.

#### ❌ "Task not found" or "Project not found"
**Solutions**:
- Verify the ID is correct
- Ensure you have access to the task/project in Asana
- Check if the task/project still exists

#### ❌ "Permission denied"
**Solutions**:
- Regenerate your Asana Personal Access Token
- Ensure your Asana account has the necessary permissions
- Update the `ASANA_PAT` secret with the new token

#### ❌ "No tasks found with tag"
**Solutions**:
- Check the tag name spelling (case-insensitive)
- Ensure tasks with that tag exist in your workspace
- Verify you have access to tagged tasks

### Debug Information

Each workflow run provides detailed logs:

1. Go to [Actions](https://github.com/deedk822-lang/The-lab-verse-monitoring-/actions)
2. Click on the specific workflow run
3. Expand the job logs to see detailed information
4. Check the "Summary Report" for an overview

## Advanced Features

### 🔧 Custom Pull Request Integration

To automatically complete tasks when PRs are merged, include task references in your PR description:

```markdown
## Description
This PR implements the new user authentication feature.

## Asana Task
asana-task-id: 1234567890

## Changes
- Added login form
- Implemented JWT authentication
- Added password reset functionality
```

### 🔧 Bulk Operations

The workflow supports different bulk operations:

- **Project-based**: Complete all tasks in specific projects
- **Tag-based**: Complete all tasks with specific tags
- **User-based**: Complete all your assigned tasks (bulk_complete)

### 🔧 Workflow Extensions

You can extend the workflow by:

1. **Adding custom notification systems**
2. **Integrating with Slack/Teams**
3. **Adding conditional logic for different project types**
4. **Creating scheduled runs for recurring completions**

## 📊 Monitoring and Analytics

Each workflow run generates:

- **Completion counts**: Number of tasks completed
- **Skip counts**: Tasks already completed
- **Error reports**: Failed operations with details
- **Summary reports**: Overview of all operations

## 🛡️ Security Best Practices

1. **Token Management**:
   - Regularly rotate your Asana Personal Access Token
   - Never commit tokens to your repository
   - Use GitHub Secrets for all sensitive data

2. **Access Control**:
   - Limit repository access to trusted team members
   - Use branch protection rules for sensitive workflows
   - Monitor workflow run logs regularly

3. **Audit Trail**:
   - All task completions are logged in workflow runs
   - Asana maintains its own activity log
   - Consider implementing additional logging if needed

## 📞 Support

If you encounter issues:

1. **Check the workflow logs** in GitHub Actions
2. **Verify your setup** using this guide
3. **Test with a single task** before bulk operations
4. **Check Asana API status** at [https://status.asana.com/](https://status.asana.com/)

## 🎉 Quick Success Test

To verify everything is working:

1. **Create a test task** in Asana
2. **Get its task ID**
3. **Run the workflow** with `single_task` action
4. **Check if the task is completed** in Asana
5. **Review the workflow logs** for success messages

---

**🚀 You're all set!** Your GitHub repository now has comprehensive Asana task completion capabilities. Start with small tests and then scale up to bulk operations as needed.
