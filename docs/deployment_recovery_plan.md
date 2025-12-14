# Enhanced Deployment Recovery Plan for The-lab-verse-monitoring

## Current Status Summary
- **Preview Deployments**: ✅ Healthy (returning 401 - authentication layer functioning as expected)
- **Production Deployment**: ❌ Failing (returning 500 - likely due to missing environment variables or dependency issue)

## Phase 1: Immediate Rollback and Verification

### 1. Emergency Rollback
Roll back the production deployment to the last known stable version.

```bash
# Find the ID of the last stable deployment (e.g., prd_xxxxxxxxxxxx)
vercel ls --prod

# Rollback to the stable deployment ID
vercel rollback [deployment-url] # Replace [deployment-url] with the actual URL of the deployment you want to rollback to.
```

### 2. Deploy to Production

```bash
# If you're not on main, create and merge a PR
# Or merge directly if appropriate
git checkout main
git pull origin main
git merge fix/linting-errors # Assuming the lint fix branch is merged
git push origin main

# Trigger Vercel deployment (might not be necessary if automatic via Git hook)
vercel --prod
```

### 3. Verify Production Deployment

```bash
# Check deployment status
vercel ls

# Once deployed, verify the public URL
curl -I https://the-lab-verse-monitoring.vercel.app/
# Expected: HTTP/1.1 200 OK
```

## Phase 2: Root Cause Analysis and Fix Implementation

### 1. Dependency Installation
Ensure all necessary dependencies are installed locally.

```bash
# Navigate to the project directory
cd The-lab-verse-monitoring-

# Install dependencies
npm install # NOTE: Ensure this is run in the correct project directory.
```

### 2. Temporary Authentication Bypass (For Testing Only)
Temporarily bypass authentication to isolate the issue from the authentication layer. **WARNING: Remove this before final production deployment.**

```javascript
// Example temporary bypass in your auth middleware
// WARNING: Remove this before final production deployment
const authMiddleware = (req, res, next) => {
  if (process.env.NODE_ENV === 'development' || req.query.bypass === 'true') {
    // TEMPORARY BYPASS FOR TESTING ONLY - REMOVE BEFORE PROD
    return next();
  }
  // ... actual authentication logic
};
```

### 3. Implement Fix
Apply the fix for the 500 error (e.g., missing dependency, incorrect API call).

```bash
# Example: Add missing dependency
npm install @octokit/rest
```

## Phase 3: Configuration and Final Testing

### 1. Local Testing
Test the fix locally with the temporary bypass enabled.

```bash
npm run dev
# Test endpoints: http://localhost:3000/api/protected?bypass=true
```

### 2. Environment Variables Configuration
Set required environment variables in Vercel. **NOTE: Redeploying is required after adding/updating environment variables in Vercel.**

```bash
# Set required environment variables in Vercel
vercel env add GITHUB_TOKEN production
vercel env add ANOTHER_SECRET production
```

### 3. Health Check Endpoint
Ensure a simple health check endpoint is available.

```javascript
// Add to your API routes
app.get('/api/health', (req, res) => {
  res.status(200).json({ status: 'ok', timestamp: new Date().toISOString() });
});
```

### 4. Authentication Middleware
Review and secure the authentication middleware. **NOTE: Consider storing the JWT securely on the client-side (e.g., using `httpOnly` cookies or secure local storage).**

```javascript
// Example JWT verification
const jwt = require('jsonwebtoken');

const authMiddleware = (req, res, next) => {
  const token = req.headers.authorization?.split(' ')[1];
  if (!token) return res.status(401).send('Access Denied');

  try {
    const verified = jwt.verify(token, process.env.JWT_SECRET);
    req.user = verified;
    next();
  } catch (err) {
    res.status(400).send('Invalid Token');
  }
};
```

## Phase 4: Final Deployment and Verification

### 1. Remove Bypass
**CRITICAL**: Remove the temporary authentication bypass from the code.

### 2. Deploy to Production
Merge the fix branch and deploy to production.

### 3. Verification Checklist
- [ ] Production deployment is successful (HTTP 200 on root).
- [ ] Health check endpoint returns `200 OK`.
- [ ] Protected endpoints return `401 Unauthorized` without a token.
- [ ] Protected endpoints return `200 OK` with a valid token.
- [ ] The `@octokit/rest` dependency is present in `package.json`.

### Testing Script

```bash
#!/bin/bash
# test-deployment.sh
# NOTE: Ensure the script is executable (`chmod +x test-deployment.sh`)

DEPLOYMENT_URL="https://the-lab-verse-monitoring.vercel.app"

echo "--- Testing Health Check ---"
health_status=$(curl -s -o /dev/null -w "%{http_code}" $DEPLOYMENT_URL/api/health)

if [ $health_status -eq 200 ]; then
  echo "✅ Health check passed (HTTP 200)"
else
  echo "❌ Health check failed (HTTP $health_status)"
  exit 1
fi

echo "--- Testing Authentication Enforcement ---"
# Test authentication
response=$(curl -s -o /dev/null -w "%{http_code}" $DEPLOYMENT_URL/api/protected)

if [ $response -eq 401 ]; then
  echo "✅ Authentication is properly enforced"
else
  echo "❌ Authentication is NOT enforced (HTTP $response)"
  exit 1
fi

echo "--- All Critical Tests Passed ---"
```

### Repository Management

```bash
# Clone or update your repository
git clone https://github.com/deedk822-lang/The-lab-verse-monitoring-.git  # Corrected URL
# Or if already cloned
git pull origin main
```
