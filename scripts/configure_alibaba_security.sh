#!/bin/bash
set -euo pipefail

echo "🔐 Configuring Alibaba Cloud Security Integration..."

# Create RAM role for GitHub Actions with proper permissions
echo "Creating RAM role for GitHub OIDC authentication..."
aliyun ram CreateRole --RoleName GitHubActionsSecurityRole --AssumeRolePolicyDocument '{
  "Statement": [{
    "Action": "sts:AssumeRoleWithOIDC",
    "Effect": "Allow",
    "Principal": {
      "Federated": "acs:ram::5212459344287865:oidc-provider/github-actions"
    },
    "Condition": {
      "StringEquals": {
        "oidc:aud": "sts.aliyuncs.com",
        "oidc:sub": "repo:deedk822-lang/The-lab-verse-monitoring-:ref:refs/heads/main"
      }
    }
  }],
  "Version": "1"
}' --Description "Role for GitHub Actions security analysis"

# Attach necessary permissions
echo "Attaching permissions to role..."
aliyun ram AttachPolicyToRole --PolicyType System --PolicyName AliyunAccessAnalyzerFullAccess --RoleName GitHubActionsSecurityRole
aliyun ram AttachPolicyToRole --PolicyType System --PolicyName AliyunECSFullAccess --RoleName GitHubActionsSecurityRole
aliyun ram AttachPolicyToRole --PolicyType System --PolicyName AliyunVPCFullAccess --RoleName GitHubActionsSecurityRole

echo "✅ Security configuration completed successfully"
echo ""
echo "Next steps:"
echo "1. Add these secrets to your GitHub repository:"
echo "   - ALIYUN_ROLE_ARN: arn:acs:ram::5212459344287865:role/GitHubActionsSecurityRole"
echo "   - ALIYUN_OIDC_PROVIDER_ARN: arn:acs:ram::5212459344287865:oidc-provider/github-actions"
echo "   - ECS_INSTANCE_ID: Your actual ECS instance ID"
echo "2. Enable the 'production' environment in your repository settings with manual approval"
