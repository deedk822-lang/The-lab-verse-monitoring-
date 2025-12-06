#!/bin/bash

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "================================================"
echo "  Lab Verse Monitoring - Fix Verification"
echo "  Date: $(date)"
echo "================================================"
echo ""

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to print success
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

# Function to print error
print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Function to print warning
print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

echo "[1/8] Checking Prerequisites..."
if command_exists node; then
    NODE_VERSION=$(node --version)
    print_success "Node.js installed: $NODE_VERSION"
else
    print_error "Node.js not installed"
fi

if command_exists python3; then
    PYTHON_VERSION=$(python3 --version)
    print_success "Python installed: $PYTHON_VERSION"
else
    print_error "Python not installed"
fi

if command_exists docker; then
    DOCKER_VERSION=$(docker --version)
    print_success "Docker installed: $DOCKER_VERSION"
else
    print_warning "Docker not installed (optional)"
fi

echo ""
echo "[2/8] Checking File Integrity..."

files=(
    "package.json"
    "vercel.json"
    ".nvmrc"
    "requirements.txt"
    "fly.toml"
    "Dockerfile"
    ".dockerignore"
)

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        print_success "$file exists"
    else
        print_error "$file missing"
    fi
done

echo ""
echo "[3/8] Checking package.json Dependencies..."

if grep -q '"@octokit/rest"' package.json; then
    print_success "@octokit/rest found in package.json"
else
    print_error "@octokit/rest missing from package.json"
fi

if grep -q '"@octokit/core"' package.json; then
    print_success "@octokit/core found in package.json"
else
    print_error "@octokit/core missing from package.json"
fi

echo ""
echo "[4/8] Checking requirements.txt..."

if grep -q '<<<<<<< HEAD' requirements.txt; then
    print_error "Merge conflict markers still present in requirements.txt"
else
    print_success "No merge conflicts in requirements.txt"
fi

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
echo "================================================"
echo "  Summary"
echo "================================================"
echo ""

echo "Next Steps:"
echo "1. Set environment variables in Vercel Dashboard"
echo "2. Set secrets in Fly.io: flyctl secrets set ..."
echo "3. Install dependencies: npm install"
echo "4. Test locally: npm start"
echo "5. Deploy to Vercel (auto-deploys on push)"
echo "6. Deploy to Fly.io: flyctl deploy"
echo ""

echo "Verification Commands:"
echo "  - Test Vercel: curl https://the-lab-verse-monitoring.vercel.app/"
echo "  - Test Fly.io: curl https://the-lab-verse-monitoring.fly.dev/health"
echo "  - Build Docker: docker build -t lab-verse ."
echo "  - Install Python: pip install -r requirements.txt"
echo ""

echo "For detailed instructions, see: FIXES_APPLIED_2025-11-11.md"
echo ""

print_success "Verification complete!"
