# Secrets Configuration Checklist

## ✅ Configured Secrets

Run `gh secret list` to see all configured secrets.

## 🔑 Critical Secrets (Required for most workflows)

- [ ] DASHSCOPE_API_KEY - Alibaba Qwen models
- [ ] OPENAI_API_KEY - OpenAI/DeepSeek
- [ ] COHERE_API_KEY - Cohere models
- [ ] HUGGINGFACE_API_KEY - HuggingFace

## 💾 Storage Secrets (Required for data persistence)

- [ ] ACCESS_KEY_ID - Alibaba OSS
- [ ] ACCESS_KEY_SECRET - Alibaba OSS

## 🔧 Optional Service Secrets

- [ ] MISTRALAI_API_KEY
- [ ] NOTION_API_KEY
- [ ] ASANA_PAT or ASANA_TOKEN
- [ ] ASANA_WORKSPACE_ID
- [ ] JIRA_USER_EMAIL
- [ ] JIRA_API_TOKEN
- [ ] JIRA_BASE_URL
- [ ] GRAFANA_TOKEN
- [ ] GLEAN_API_KEY
- [ ] GLEAN_API_ENDPOINT

## 📱 Marketing & Integration Secrets

- [ ] WORDPRESS_USER
- [ ] WORDPRESS_PASSWORD
- [ ] MAILCHIMP_API_KEY
- [ ] ARYSHARE_API_KEY
- [ ] MANAGE_WIX_API_KEY

## 📊 Data & Analytics Secrets

- [ ] KAGGLE_USERNAME
- [ ] KAGGLE_API_KEY

## 🔍 How to Get These Secrets

### Alibaba Cloud (Qwen)
1. Visit: https://dashscope.aliyuncs.com/
2. Sign up / Log in
3. Go to API Keys section
4. Create new API key

### OpenAI
1. Visit: https://platform.openai.com/api-keys
2. Create new secret key
3. Copy immediately (won't show again)

### Cohere
1. Visit: https://dashboard.cohere.ai/api-keys
2. Create new API key

### HuggingFace
1. Visit: https://huggingface.co/settings/tokens
2. Create new token with "read" permissions

### Asana
1. Visit: https://app.asana.com/0/developer-console
2. Create Personal Access Token
3. For Workspace ID, check URL when viewing Asana

### Notion
1. Visit: https://www.notion.so/my-integrations
2. Create new integration
3. Copy Internal Integration Token

### Jira
1. Visit: https://id.atlassian.com/manage-profile/security/api-tokens
2. Create API token
3. Base URL is your Jira instance (e.g., https://your-domain.atlassian.net)

## 🚨 Security Notes

- ⚠️ Never commit secrets to git
- ⚠️ Rotate secrets regularly
- ⚠️ Use least-privilege access
- ⚠️ Monitor secret usage in workflows
- ⚠️ Delete unused secrets

## 📖 References

- GitHub Secrets Docs: https://docs.github.com/en/actions/security-guides/encrypted-secrets
- Repository Settings: https://github.com/deedk822-lang/The-lab-verse-monitoring-/settings/secrets/actions

---
Generated: $(date)
