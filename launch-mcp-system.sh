#!/bin/bash

###############################################################################
# The Lab-Verse Monitoring System - MCP Integration Launch Script
# 
# This script initializes and launches the complete workflow automation system
# with all MCP integrations (Asana, Notion, Airtable, Gmail, Hugging Face)
###############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Log functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Header
echo "============================================================================"
echo "  The Lab-Verse Monitoring System - MCP Integration Launcher"
echo "============================================================================"
echo ""

# Check if running from correct directory
if [ ! -f "package.json" ]; then
    log_error "Must run from project root directory"
    exit 1
fi

# Load environment variables
log_info "Loading environment variables..."
if [ -f ".env" ]; then
    source .env
    log_success "Loaded .env"
else
    log_warning ".env file not found, using defaults"
fi

if [ -f ".env.mcp" ]; then
    source .env.mcp
    log_success "Loaded .env.mcp"
else
    log_warning ".env.mcp file not found"
fi

# Check Node.js version
log_info "Checking Node.js version..."
NODE_VERSION=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 18 ]; then
    log_error "Node.js 18+ required (found v$NODE_VERSION)"
    exit 1
fi
log_success "Node.js version OK (v$(node --version))"

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    log_info "Installing dependencies..."
    npm install
    log_success "Dependencies installed"
else
    log_info "Dependencies already installed"
fi

# Verify MCP CLI is available
log_info "Verifying MCP CLI..."
if ! command -v manus-mcp-cli &> /dev/null; then
    log_error "manus-mcp-cli not found. Please ensure it's installed."
    exit 1
fi
log_success "MCP CLI available"

# Test MCP server connections
log_info "Testing MCP server connections..."

test_mcp_server() {
    local server=$1
    log_info "  Testing $server..."
    if timeout 10 manus-mcp-cli tool list --server "$server" &> /dev/null; then
        log_success "  $server: Connected"
        return 0
    else
        log_warning "  $server: Not available or timeout"
        return 1
    fi
}

# Test each MCP server
ASANA_OK=false
NOTION_OK=false
AIRTABLE_OK=false
GMAIL_OK=false
HUGGINGFACE_OK=false

test_mcp_server "asana" && ASANA_OK=true
test_mcp_server "notion" && NOTION_OK=true
test_mcp_server "airtable" && AIRTABLE_OK=true
test_mcp_server "gmail" && GMAIL_OK=true
test_mcp_server "hugging-face" && HUGGINGFACE_OK=true

# Summary of MCP connections
echo ""
log_info "MCP Server Status Summary:"
echo "  Asana:        $([ "$ASANA_OK" = true ] && echo "✅" || echo "❌")"
echo "  Notion:       $([ "$NOTION_OK" = true ] && echo "✅" || echo "❌")"
echo "  Airtable:     $([ "$AIRTABLE_OK" = true ] && echo "✅" || echo "❌")"
echo "  Gmail:        $([ "$GMAIL_OK" = true ] && echo "✅" || echo "❌")"
echo "  Hugging Face: $([ "$HUGGINGFACE_OK" = true ] && echo "✅" || echo "❌")"
echo ""

# Check critical environment variables
log_info "Verifying environment configuration..."

check_env_var() {
    local var_name=$1
    local var_value="${!var_name}"
    
    if [ -z "$var_value" ] || [ "$var_value" = "your_*_here" ]; then
        log_warning "  $var_name: Not configured"
        return 1
    else
        log_success "  $var_name: Configured"
        return 0
    fi
}

# Check critical variables
CRITICAL_VARS=(
    "ASANA_WORKSPACE_ID"
    "NOTION_WORKSPACE_ID"
    "AIRTABLE_BASE_METRICS"
    "GMAIL_SENDER_EMAIL"
)

MISSING_VARS=0
for var in "${CRITICAL_VARS[@]}"; do
    check_env_var "$var" || ((MISSING_VARS++))
done

if [ $MISSING_VARS -gt 0 ]; then
    log_warning "$MISSING_VARS critical environment variables not configured"
    log_info "Please update .env.mcp with your actual values"
fi

echo ""
log_info "============================================================================"
log_info "System Launch Options:"
log_info "============================================================================"
echo ""
echo "  1. Launch Full System (All Workflows)"
echo "  2. Test Individual Workflow"
echo "  3. Setup Wizard (Configure Notion/Asana/Airtable)"
echo "  4. Run System Verification"
echo "  5. Exit"
echo ""
read -p "Select option (1-5): " OPTION

case $OPTION in
    1)
        log_info "Launching full system..."
        node src/mcp-orchestrator.js
        ;;
    2)
        log_info "Available workflows:"
        echo "  1. SEO Ranking Drop Response"
        echo "  2. High-Performing Content Amplification"
        echo "  3. Crisis Event Response"
        echo "  4. B2B Client Onboarding"
        echo "  5. Weekly Performance Report"
        read -p "Select workflow (1-5): " WORKFLOW
        
        case $WORKFLOW in
            1)
                log_info "Testing SEO Ranking Drop workflow..."
                node -e "
                const MCPOrchestrator = require('./src/mcp-orchestrator.js');
                const orch = new MCPOrchestrator();
                orch.initialize().then(() => {
                    return orch.handleSEORankingDrop('african trade policy', 3, 8, 'https://example.com/article');
                }).then(() => {
                    console.log('Test completed successfully');
                }).catch(err => {
                    console.error('Test failed:', err);
                    process.exit(1);
                });
                "
                ;;
            2)
                log_info "Testing Content Amplification workflow..."
                node -e "
                const MCPOrchestrator = require('./src/mcp-orchestrator.js');
                const orch = new MCPOrchestrator();
                orch.initialize().then(() => {
                    return orch.amplifyHighPerformingContent('Test Article', 'https://example.com/article', 0.18, 250);
                }).then(() => {
                    console.log('Test completed successfully');
                }).catch(err => {
                    console.error('Test failed:', err);
                    process.exit(1);
                });
                "
                ;;
            5)
                log_info "Generating weekly report..."
                node -e "
                const MCPOrchestrator = require('./src/mcp-orchestrator.js');
                const orch = new MCPOrchestrator();
                orch.initialize().then(() => {
                    return orch.generateWeeklyReport();
                }).then(() => {
                    console.log('Report generated successfully');
                }).catch(err => {
                    console.error('Report generation failed:', err);
                    process.exit(1);
                });
                "
                ;;
            *)
                log_error "Invalid workflow selection"
                exit 1
                ;;
        esac
        ;;
    3)
        log_info "Launching setup wizard..."
        node scripts/setup-wizard.js
        ;;
    4)
        log_info "Running system verification..."
        
        # Verify all components
        log_info "Verifying MCP integrations..."
        
        # Test Asana
        if [ "$ASANA_OK" = true ]; then
            log_info "Testing Asana workspace access..."
            if [ -n "$ASANA_WORKSPACE_ID" ] && [ "$ASANA_WORKSPACE_ID" != "your_workspace_gid_here" ]; then
                log_success "Asana workspace configured"
            else
                log_warning "Asana workspace ID not configured"
            fi
        fi
        
        # Test Notion
        if [ "$NOTION_OK" = true ]; then
            log_info "Testing Notion workspace access..."
            if [ -n "$NOTION_WORKSPACE_ID" ] && [ "$NOTION_WORKSPACE_ID" != "your_workspace_id_here" ]; then
                log_success "Notion workspace configured"
            else
                log_warning "Notion workspace ID not configured"
            fi
        fi
        
        # Test Airtable
        if [ "$AIRTABLE_OK" = true ]; then
            log_info "Testing Airtable base access..."
            if [ -n "$AIRTABLE_BASE_METRICS" ] && [ "$AIRTABLE_BASE_METRICS" != "your_base_id_here" ]; then
                log_success "Airtable base configured"
            else
                log_warning "Airtable base ID not configured"
            fi
        fi
        
        log_success "System verification completed"
        ;;
    5)
        log_info "Exiting..."
        exit 0
        ;;
    *)
        log_error "Invalid option"
        exit 1
        ;;
esac

log_success "Operation completed successfully!"
