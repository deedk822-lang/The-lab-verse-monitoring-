# 🚀 GitHub Actions Workflow Setup Guide

## Quick Setup (5 minutes)

### Step 1: Add GitHub Secrets

Go to: `Settings → Secrets and variables → Actions`

**Minimum Required:**
```bash
VERCEL_TOKEN=<get from https://vercel.com/account/tokens>
VERCEL_ORG_ID=<from Vercel project settings>
VERCEL_PROJECT_ID=<from Vercel project settings>
```

### Step 2: Verify Workflow

After merging this PR, the workflow will automatically run.

Monitor at: `Actions` tab in GitHub

### Step 3: Troubleshooting

**If workflow fails:**

1. Check the Actions tab for error logs
2. Verify all secrets are set correctly
3. Ensure package.json has the required scripts
4. Test locally: `npm ci && npm run build`

## Workflow Triggers

- **Push to main**: Full CI/CD + production deployment
- **Pull Request**: Full CI/CD + preview deployment
- **Manual**: Can trigger via Actions tab

## Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| Missing secrets | Add them in repository Settings |
| Build fails | Check package.json scripts |
| Tests fail | Run `npm test` locally first |
| Deployment timeout | Increase timeout in workflow |

## Next Steps

1. ✅ Merge this PR
2. ✅ Add GitHub secrets
3. ✅ Monitor first workflow run
4. ✅ Test deployment
5. ✅ Configure branch protection (optional)

## Support

- Workflow issues: Check Actions tab logs
- Deployment issues: Check Vercel dashboard
- Other issues: Create a GitHub issue

---

**Status**: Ready for production use
