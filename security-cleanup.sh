#!/bin/bash
set -e

echo "🔒 Starting Security & Hygiene Cleanup..."

# 1. Secure Environment Files
# Move .env files to a secure backup directory outside git if they contain real secrets
# For now, we just ensure they are ignored and examples are standardized.
mkdir -p secrets_backup
if [ -f ".env.local" ]; then
    echo "⚠️  Found .env.local. Moving to secrets_backup/ (DO NOT COMMIT THIS FOLDER)"
    mv .env.local secrets_backup/
fi

# 2. Generate robust .gitignore
echo "📄 Generating production .gitignore..."
cat > .gitignore << 'EOF'
# Secrets & Environment
.env
.env.local
.env.*.local
secrets_backup/
*.pem
*.key
*.p12

# Dependencies
node_modules/
__pycache__/
*.pyc
.venv/
venv/
target/
dist/
build/
vendor/

# IDEs
.idea/
.vscode/
*.swp
.DS_Store

# Logs
logs/
*.log
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# OS Generated
.DS_Store
Thumbs.db

# Project Specific
.vercel/
.next/
.serverless/
.jules/logs/
EOF

echo "✅ Security cleanup complete. Check 'secrets_backup/' if you need your old env vars."
