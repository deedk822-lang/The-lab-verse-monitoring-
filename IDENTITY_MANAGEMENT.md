# 🆔 Vaal AI Empire - Identity Management

## Overview

The Vaal AI Empire uses **three separate identities** to prevent authentication conflicts and maintain clear separation of concerns across different services.

---

## 📋 The Three Personas

### 1️⃣ DEEDK822 (Blog Owner & Content Publisher)

**Email:** `deedk822@gmail.com`  
**WordPress:** `deedk822.wordpress.com`  
**Purpose:** Content publishing & SEO

**Services:**
- WordPress blog publishing
- Content distribution
- SEO optimization

**GitHub Secrets Required:**
- `WORDPRESS_USER` = `deedk822@gmail.com`
- `WORDPRESS_PASSWORD` = WordPress Application Password

**Workflows Using This Identity:**
- `.github/workflows/authority-engine.yml`
- `.github/workflows/content-pipeline.yml`

---

### 2️⃣ LUNGELO LUDA (Data Analyst)

**Email:** `dimakatsomoleli@gmail.com`  
**Kaggle Username:** `lungeloluda`  
**Purpose:** Dataset intelligence gathering

**Services:**
- Kaggle dataset discovery
- Market research data collection
- Competitive intelligence

**GitHub Secrets Required:**
- `KAGGLE_USERNAME` = `lungeloluda`
- `KAGGLE_API_KEY` = Kaggle API Token

**Workflows Using This Identity:**
- `.github/workflows/kaggle-intelligence.yml`

---

### 3️⃣ DIMAKATSO MOLELI (Project Manager)

**Email:** `dimakatsomoleli@gmail.com`  
**Jira:** `dimakatsomoleli.atlassian.net`  
**Purpose:** Task tracking & workflow management

**Services:**
- Jira ticket creation
- Project tracking
- Workflow automation

**GitHub Secrets Required:**
- `JIRA_USER_EMAIL` = `dimakatsomoleli@gmail.com`
- `JIRA_API_TOKEN` = Jira API Token
- `JIRA_LINK` = Same as `JIRA_API_TOKEN` (legacy name)

**Workflows Using This Identity:**
- `.github/workflows/kaggle-intelligence.yml` (creates tickets)
- `.github/workflows/authority-engine.yml` (logs work)

---

## 🔑 GitHub Secrets Configuration

### Required Secrets

Go to: `https://github.com/deedk822-lang/The-lab-verse-monitoring-/settings/secrets/actions`

| Secret Name | Value | Used By |
|-------------|-------|----------|
| `WORDPRESS_USER` | `deedk822@gmail.com` | Authority Engine |
| `WORDPRESS_PASSWORD` | WordPress App Password | Authority Engine |
| `KAGGLE_USERNAME` | `lungeloluda` | Kaggle Intelligence |
| `KAGGLE_API_KEY` | Kaggle API Token | Kaggle Intelligence |
| `JIRA_USER_EMAIL` | `dimakatsomoleli@gmail.com` | Multiple Workflows |
| `JIRA_LINK` | Jira API Token | Multiple Workflows |

### How to Get API Tokens

**WordPress Application Password:**
1. Log in to WordPress.com as `deedk822@gmail.com`
2. Go to Settings → Security → Application Passwords
3. Create new password named "GitHub Actions"
4. Copy the generated password

**Kaggle API Key:**
1. Log in to Kaggle.com as `lungeloluda`
2. Go to Account → API → Create New Token
3. Download `kaggle.json`
4. Use the `key` value from the JSON file

**Jira API Token:**
1. Log in to Atlassian as `dimakatsomoleli@gmail.com`
2. Go to Account Settings → Security → API Tokens
3. Create token named "Vaal AI Empire"
4. Copy the generated token

---

## ⚠️ Common Mistakes to Avoid

### ❌ DON'T: Mix Identities

```yaml
# BAD - Using wrong email for Kaggle
KAGGLE_USERNAME: deedk822@gmail.com  # WRONG!
```

### ✅ DO: Use Correct Identity per Service

```yaml
# GOOD - Correct identity mapping
KAGGLE_USERNAME: lungeloluda        # Lungelo Luda
JIRA_USER_EMAIL: dimakatsomoleli@gmail.com  # Dimakatso
WORDPRESS_USER: deedk822@gmail.com  # Deedk822
```

---

## 🛠️ Troubleshooting

### Workflow Fails with "Authentication Failed"

**Cause:** Wrong identity used for service

**Fix:**
1. Check which service is failing (WordPress, Kaggle, or Jira)
2. Verify the correct email/username is in GitHub Secrets
3. Confirm API token is still valid

### Kaggle Says "User Not Found"

**Cause:** Using `dimakatsomoleli@gmail.com` as Kaggle username

**Fix:**
```yaml
# Change from:
KAGGLE_USERNAME: ${{ secrets.JIRA_USER_EMAIL }}  # WRONG

# To:
KAGGLE_USERNAME: ${{ secrets.KAGGLE_USERNAME }}  # CORRECT (lungeloluda)
```

### WordPress Rejects Login

**Cause:** Using Jira/Kaggle credentials for WordPress

**Fix:**
```yaml
# Ensure WordPress uses its own identity:
WORDPRESS_USER: deedk822@gmail.com  # NOT dimakatsomoleli@gmail.com
```

---

## 📊 Identity Usage Matrix

| Service | Email | Username | Password/Token |
|---------|-------|----------|----------------|
| **WordPress** | deedk822@gmail.com | N/A | Application Password |
| **Kaggle** | dimakatsomoleli@gmail.com | lungeloluda | API Key |
| **Jira** | dimakatsomoleli@gmail.com | N/A | API Token |
| **OSS** | N/A | Access Key ID | Secret Key |

---

## 📦 Files Related to Identity Management

- `vaal-ai-empire/scripts/correct_identities.sh` - Identity documentation script
- `vaal-ai-empire/.env.example` - Environment variable template
- `.github/workflows/kaggle-intelligence.yml` - Uses Lungelo + Dimakatso
- `.github/workflows/authority-engine.yml` - Uses Deedk822 + Dimakatso
- `IDENTITY_MANAGEMENT.md` - This file

---

## ✅ Verification Checklist

Before running workflows, verify:

- [ ] `WORDPRESS_USER` = `deedk822@gmail.com`
- [ ] `KAGGLE_USERNAME` = `lungeloluda`
- [ ] `JIRA_USER_EMAIL` = `dimakatsomoleli@gmail.com`
- [ ] All API tokens are valid and not expired
- [ ] No workflows use generic `USER_LOGON_NAME` variable
- [ ] Each workflow explicitly declares which identity it uses

---

## 📝 Maintenance

### When to Update Credentials

**WordPress Password:**
- Every 90 days (security best practice)
- Immediately if compromised

**Kaggle API Key:**
- When changing Kaggle account settings
- If key is leaked or compromised

**Jira API Token:**
- Every 6 months (Atlassian recommendation)
- When team members change

### How to Update

1. Generate new token/password from service
2. Update GitHub Secret immediately
3. Test workflow to confirm it works
4. Revoke old token/password

---

## 🔗 Quick Links

- [GitHub Secrets Settings](https://github.com/deedk822-lang/The-lab-verse-monitoring-/settings/secrets/actions)
- [WordPress.com Account](https://wordpress.com/me/security)
- [Kaggle API Settings](https://www.kaggle.com/settings/account)
- [Jira API Tokens](https://id.atlassian.com/manage-profile/security/api-tokens)

---

## ❓ Questions?

If workflows fail with authentication errors:

1. Run `./vaal-ai-empire/scripts/correct_identities.sh` to see identity mapping
2. Check GitHub Actions logs for which service failed
3. Verify the correct identity is configured in workflow YAML
4. Confirm secrets in GitHub match the persona for that service

---

**Last Updated:** December 13, 2025  
**Maintained by:** Vaal AI Empire Operations
