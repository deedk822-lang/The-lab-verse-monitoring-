#!/bin/bash
set -e

echo "🆔 CORRECTING EMPIRE IDENTITIES (SPLIT PERSONAS)..."

# 1. WORDPRESS IDENTITY (deedk822)
export WORDPRESS_USER="deedk822@gmail.com"
export WORDPRESS_URL="https://deedk822.wordpress.com/xmlrpc.php"

# 2. KAGGLE IDENTITY (Lungelo Luda)
# API requires lowercase/no spaces usually
export KAGGLE_USERNAME="lungeloluda"
# (Kaggle auth uses the key, but we note the email for record)
export KAGGLE_EMAIL="dimakatsomoleli@gmail.com"

# 3. JIRA IDENTITY (Dimakatso)
export JIRA_USER_EMAIL="dimakatsomoleli@gmail.com"
export JIRA_BASE_URL="https://dimakatsomoleli.atlassian.net"

# 4. UPDATE .ENV FILE PERMANENTLY
# Remove old wrong entries
sed -i '/WORDPRESS_USER/d' vaal-ai-empire/.env
sed -i '/KAGGLE_USERNAME/d' vaal-ai-empire/.env
sed -i '/JIRA_USER_EMAIL/d' vaal-ai-empire/.env

# Add corrected entries
cat << EOF >> vaal-ai-empire/.env

# --- CORRECTED IDENTITIES ---
# Blog Owner
WORDPRESS_USER=deedk822@gmail.com
WORDPRESS_URL=https://deedk822.wordpress.com/xmlrpc.php

# Data Analyst
KAGGLE_USERNAME=lungeloluda

# Project Manager
JIRA_USER_EMAIL=dimakatsomoleli@gmail.com
EOF

echo "✅ IDENTITIES SPLIT AND FIXED."
echo "   - WordPress posts as: deedk822@gmail.com"
echo "   - Kaggle runs as:     lungeloluda"
echo "   - Jira logs as:       dimakatsomoleli@gmail.com"
