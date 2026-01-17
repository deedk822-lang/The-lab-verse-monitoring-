#!/bin/bash
set -euo pipefail

echo "🔐 Configuring Alibaba Cloud Security Integration..."

# Create RAM role for GitHub Actions
echo "Creating RAM role for GitHub OIDC authentication..."
aliyun ram CreateRole --RoleName GitHubActionsSecurityRole --AssumeRolePolicyDocument '{
  "Statement": [{
    "Action": "sts:AssumeRoleWithOIDC",
    "Effect": "Allow",
    "Principal": {
      "Federated": "acs:ram::<your-account-id>:oidc-provider/github-actions"
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

# Attach Access Analyzer permissions
echo "Attaching Access Analyzer permissions..."
aliyun ram AttachPolicyToRole --PolicyType System --PolicyName AliyunAccessAnalyzerFullAccess --RoleName GitHubActionsSecurityRole

echo "✅ Security configuration completed successfully"
echo ""
echo "Next steps:"
echo "1. Add these secrets to your GitHub repository:"
echo "   - ALIYUN_ROLE_ARN: arn:acs:ram::<your-account-id>:role/GitHubActionsSecurityRole"
echo "   - ALIYUN_OIDC_PROVIDER_ARN: arn:acs:ram::<your-account-id>:oidc-provider/github-actions"
echo "2. Enable the 'production' environment in your repository settings with manual approval"
