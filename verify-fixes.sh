#!/bin/bash

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

if grep -q '^groq$' requirements.txt; then
    print_success "groq dependency correctly formatted"
else
    print_warning "groq dependency might need verification"
fi

echo ""
echo "[5/8] Checking fly.toml Configuration..."

if grep -q 'force_https = true' fly.toml | grep -v '#'; then
    FORCE_HTTPS_COUNT=$(grep -c 'force_https = true' fly.toml)
    if [ "$FORCE_HTTPS_COUNT" -eq 1 ]; then
        print_success "Single force_https configuration (correct)"
    else
        print_warning "Multiple force_https found - verify TLS config"
    fi
fi

echo ""
echo "[6/8] Testing Node.js Module Resolution..."

if [ -d "node_modules" ]; then
    if [ -d "node_modules/@octokit/rest" ]; then
        print_success "@octokit/rest installed in node_modules"
    else
        print_warning "@octokit/rest not installed - run: npm install"
    fi
else
    print_warning "node_modules not found - run: npm install"
fi

echo ""
echo "[7/8] Checking Docker Configuration..."

if grep -q 'WORKDIR /app' Dockerfile; then
    print_success "WORKDIR set correctly in Dockerfile"
fi

if grep -q 'mkdir -p /app/runtime' Dockerfile; then
    print_success "Runtime directory creation found"
fi

if [ -f ".dockerignore" ]; then
    if grep -q 'node_modules' .dockerignore; then
        print_success ".dockerignore properly configured"
    fi
fi

echo ""
echo "[8/8] Checking Git Status..."

if git rev-parse --git-dir > /dev/null 2>&1; then
    print_success "Git repository detected"
    
    if git diff-index --quiet HEAD --; then
        print_success "No uncommitted changes"
    else
        print_warning "Uncommitted changes detected"
    fi
    
    CURRENT_BRANCH=$(git branch --show-current)
    print_success "Current branch: $CURRENT_BRANCH"
else
    print_error "Not a git repository"
fi

echo ""
