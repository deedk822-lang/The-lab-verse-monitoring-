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
 dual-agent-cicd-pipeline-1349139378403618497
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

}' --Description "Role for GitHub Actions security analysis and deployment"

# Create and attach custom policy for ECS deployment permissions
echo "Creating custom ECS deployment policy..."
CUSTOM_POLICY_NAME="GitHubActionsEcsDeploymentPolicy"

# Define the custom policy document
CUSTOM_POLICY_DOC='{
  "Version": "1",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ecs:DescribeInstances",
        "ecs:RunCommand",
        "ecs:DescribeInstanceStatus"
      ],
      "Resource": "*"
    }
  ]
}'

aliyun ram CreatePolicy --PolicyName "${CUSTOM_POLICY_NAME}" --PolicyDocument "${CUSTOM_POLICY_DOC}"

# Attach the custom policy to the role
aliyun ram AttachPolicyToRole --PolicyName "${CUSTOM_POLICY_NAME}" --PolicyType "Custom" --RoleName "GitHubActionsSecurityRole"

# Attach system policies for Access Analyzer and read-only access
aliyun ram AttachPolicyToRole --PolicyName "AliyunAccessAnalyzerFullAccess" --PolicyType "System" --RoleName "GitHubActionsSecurityRole"
aliyun ram AttachPolicyToRole --PolicyName "AliyunReadOnlyAccess" --PolicyType "System" --RoleName "GitHubActionsSecurityRole"

echo "✅ Security configuration complete."
echo "ARN for the role 'GitHubActionsSecurityRole' is ready to be used in GitHub Secrets."
 feat/type-safe-ci-cd-11076003968485077177
