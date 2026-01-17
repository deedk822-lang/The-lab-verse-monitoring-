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
