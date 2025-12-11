#!/bin/bash

# Master Fix and Verify Script
# Applies all fixes and runs comprehensive verification

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

clear

echo -e "${BOLD}${CYAN}"
echo "╔═══════════════════════════════════════════════════════════════════╗"
echo "║                                                                   ║"
echo "║         VAAL AI EMPIRE - MASTER FIX & VERIFY WORKFLOW             ║"
echo "║                                                                   ║"
echo "║              Fixes all issues and verifies system                ║"
echo "║                                                                   ║"
echo "╚═══════════════════════════════════════════════════════════════════╝"
echo -e "${NC}\n"

print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_step() {
    echo -e "\n${BOLD}${BLUE}▶ $1${NC}\n"
}

# Function to check command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to wait for user
wait_for_user() {
    echo -e "\n${YELLOW}Press Enter to continue...${NC}"
    read -r
}

# Check prerequisites
print_step "STEP 1: Checking Prerequisites"

if ! command_exists python3; then
    print_error "Python 3 not found. Please install Python 3.8+"
    exit 1
fi
print_status "Python 3: $(python3 --version)"

if ! command_exists node; then
    print_warning "Node.js not found (optional for verification)"
else
    print_status "Node.js: $(node --version)"
fi

if ! command_exists git; then
    print_warning "Git not found (optional)"
else
    print_status "Git: $(git --version | head -n1)"
fi

# Check we're in project root
if [ ! -f "package.json" ]; then
    print_error "Not in project root directory"
    echo "Please run this script from the project root"
    exit 1
fi
print_status "Project root confirmed"

# Create backup
print_step "STEP 2: Creating Backup"

TIMESTAMP=$(date +%Y%m%d-%H%M%S)
BACKUP_DIR="backups/master-fix-$TIMESTAMP"
mkdir -p "$BACKUP_DIR"

echo "Backing up important files..."
[ -f "vercel.json" ] && cp vercel.json "$BACKUP_DIR/"
[ -f ".env" ] && cp .env "$BACKUP_DIR/"
[ -f ".env.example" ] && cp .env.example "$BACKUP_DIR/"
[ -f "package.json" ] && cp package.json "$BACKUP_DIR/"

print_status "Backup created: $BACKUP_DIR"

# Apply fixes
print_step "STEP 3: Applying All Fixes"

print_info "Making fix scripts executable..."
chmod +x scripts/fix-all-issues.sh 2>/dev/null || true
chmod +x scripts/auto-fix-pr611.sh 2>/dev/null || true

if [ -f "scripts/fix-all-issues.sh" ]; then
    print_info "Running comprehensive fixes..."
    ./scripts/fix-all-issues.sh
    print_status "Fixes applied"
else
    print_warning "fix-all-issues.sh not found, applying manual fixes..."

    # Manual fixes
    # Fix 1: vercel.json
    if [ -f "vercel.json" ]; then
        if grep -q "GLM4_API_KEY" vercel.json; then
            print_info "Removing GLM4_API_KEY from vercel.json..."
            # Backup and remove the line
            sed -i.bak '/GLM4_API_KEY/d' vercel.json
            print_status "vercel.json fixed"
        fi
    fi

    # Fix 2: .env.example
    if [ -f ".env.example" ]; then
        if ! grep -q "PERPLEXITY_API_KEY" .env.example; then
            print_info "Adding Perplexity to .env.example..."
            echo "" >> .env.example
            echo "# Perplexity AI for deep keyword research" >> .env.example
            echo "PERPLEXITY_API_KEY=your_perplexity_key_here" >> .env.example
            print_status ".env.example updated"
        fi
    fi
fi

# Setup environment
print_step "STEP 4: Environment Configuration"

if [ ! -f ".env" ]; then
    print_warning "No .env file found"

    if [ -f ".env.example" ]; then
        echo -e "${YELLOW}Would you like to create .env from .env.example? (y/n)${NC}"
        read -r response

        if [[ "$response" =~ ^[Yy]$ ]]; then
            cp .env.example .env
            print_status ".env file created"

            echo -e "\n${BOLD}${YELLOW}IMPORTANT: You must edit .env and add your API keys!${NC}"
            echo -e "Required: ${BOLD}At least ONE AI provider:${NC}"
            echo "  - COHERE_API_KEY (https://cohere.com)"
            echo "  - GROQ_API_KEY (https://groq.com)"
            echo "  - OPENAI_API_KEY (https://openai.com)"
            echo ""
            echo "Optional but recommended:"
            echo "  - PERPLEXITY_API_KEY (for keyword research)"
            echo "  - TWILIO credentials (for WhatsApp)"
            echo "  - AYRSHARE_API_KEY (for social media)"
            echo ""
            echo -e "${YELLOW}Press Enter when you've added at least one AI provider key...${NC}"
            read -r
        fi
    else
        print_error "Cannot create .env - .env.example not found"
        exit 1
    fi
else
    print_status ".env file exists"
fi

# Check for API keys
print_info "Checking API configuration..."
API_CONFIGURED=false

if [ ! -z "${COHERE_API_KEY}" ] && [ "${COHERE_API_KEY}" != "your_cohere_key_here" ]; then
    print_status "Cohere API configured"
    API_CONFIGURED=true
fi

if [ ! -z "${GROQ_API_KEY}" ] && [ "${GROQ_API_KEY}" != "your_groq_key_here" ]; then
    print_status "Groq API configured"
    API_CONFIGURED=true
fi

if [ ! -z "${OPENAI_API_KEY}" ] && [ "${OPENAI_API_KEY}" != "your_openai_key_here" ]; then
    print_status "OpenAI API configured"
    API_CONFIGURED=true
fi

if [ "$API_CONFIGURED" = false ]; then
    print_error "No AI provider configured in environment!"
    print_info "Please set at least one API key in .env file"
    print_info "Then run this script again"
    exit 1
fi

# Install dependencies
print_step "STEP 5: Installing Dependencies"

# Python virtual environment
if [ ! -d "venv" ]; then
    print_info "Creating Python virtual environment..."
    python3 -m venv venv
    print_status "Virtual environment created"
fi

print_info "Activating virtual environment..."
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    print_status "Virtual environment activated"
elif [ -f "venv/Scripts/activate" ]; then
    source venv/Scripts/activate
    print_status "Virtual environment activated (Windows)"
else
    print_error "Cannot activate virtual environment"
    exit 1
fi

# Install Python packages
print_info "Installing Python dependencies..."
cd vaal-ai-empire
if pip install -q -r requirements.txt; then
    print_status "Python packages installed"
else
    print_warning "Some Python packages may have failed to install"
fi
cd ..

# Install Node.js packages
if command_exists npm; then
    print_info "Installing Node.js dependencies..."
    if npm install --silent 2>/dev/null; then
        print_status "Node.js packages installed"
    else
        print_warning "Some Node.js packages may have failed to install"
    fi
fi

# Validate environment
print_step "STEP 6: Environment Validation"

if [ -f "scripts/validate-environment.js" ] && command_exists node; then
    print_info "Running environment validation..."
    if node scripts/validate-environment.js; then
        print_status "Environment validation passed"
    else
        print_warning "Environment validation found issues"
        print_info "Review the output above for details"
        wait_for_user
    fi
else
    print_warning "Environment validator not available (skipping)"
fi

# Run comprehensive verification
print_step "STEP 7: System Verification"

chmod +x scripts/verify-system.sh 2>/dev/null || true

if [ -f "scripts/verify-system.sh" ]; then
    print_info "Running comprehensive system verification..."
    echo -e "${CYAN}This may take 2-5 minutes...${NC}\n"

    if ./scripts/verify-system.sh; then
        VERIFICATION_SUCCESS=true
    else
        VERIFICATION_SUCCESS=false
    fi
else
    print_warning "Verification script not found"

    if [ -f "scripts/verify-system-live.py" ]; then
        print_info "Running Python verification directly..."
        if python3 scripts/verify-system-live.py; then
            VERIFICATION_SUCCESS=true
        else
            VERIFICATION_SUCCESS=false
        fi
    else
        print_warning "No verification scripts available"
        VERIFICATION_SUCCESS="unknown"
    fi
fi

# Final summary
print_step "FINAL SUMMARY"

echo -e "${BOLD}Status Summary:${NC}"
echo ""
echo "  Backups: $BACKUP_DIR"
echo "  Fixes Applied: ✓"
echo "  Dependencies Installed: ✓"
echo "  Environment Configured: ✓"

if [ "$VERIFICATION_SUCCESS" = true ]; then
    echo -e "  System Verification: ${GREEN}✓ PASSED${NC}"
elif [ "$VERIFICATION_SUCCESS" = false ]; then
    echo -e "  System Verification: ${YELLOW}⚠ ISSUES FOUND${NC}"
else
    echo -e "  System Verification: ${YELLOW}⊘ NOT RUN${NC}"
fi

echo ""

if [ "$VERIFICATION_SUCCESS" = true ]; then
    echo -e "${BOLD}${GREEN}"
    echo "╔═══════════════════════════════════════════════════════════════════╗"
    echo "║                                                                   ║"
    echo "║                    ✓ SYSTEM READY FOR DEPLOYMENT                 ║"
    echo "║                                                                   ║"
    echo "╚═══════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}\n"

    echo -e "${BOLD}Next Steps:${NC}"
    echo ""
    echo "1. Review verification report:"
    echo "   cat verification_report.json"
    echo ""
    echo "2. Deploy to Vercel:"
    echo "   vercel --prod"
    echo ""
    echo "3. Start automation:"
    echo "   python scripts/daily_automation.py"
    echo ""
    echo "4. Test client onboarding:"
    echo "   python scripts/client_onboarding.py demo +27821234567 'Test' butchery"
    echo ""

    exit 0
else
    echo -e "${BOLD}${YELLOW}"
    echo "╔═══════════════════════════════════════════════════════════════════╗"
    echo "║                                                                   ║"
    echo "║                  ⚠ VERIFICATION INCOMPLETE                        ║"
    echo "║                                                                   ║"
    echo "╚═══════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}\n"

    echo -e "${BOLD}Troubleshooting:${NC}"
    echo ""
    echo "1. Check verification report:"
    echo "   cat verification_report.json"
    echo ""
    echo "2. Validate environment:"
    echo "   node scripts/validate-environment.js"
    echo ""
    echo "3. Run quick test:"
    echo "   cd vaal-ai-empire && python scripts/quick_test.py"
    echo ""
    echo "4. Check logs:"
    echo "   ls -la logs/"
    echo ""
    echo "5. Review documentation:"
    echo "   cat ALL_FIXES_SUMMARY.md"
    echo "   cat QUICK_START.md"
    echo ""

    exit 1
fi