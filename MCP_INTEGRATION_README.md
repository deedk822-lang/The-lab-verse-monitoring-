# The Lab-Verse Monitoring System - MCP Integration

## Overview

This system integrates **Model Context Protocol (MCP)** servers to create a fully automated workflow for content intelligence, crisis response, SEO monitoring, and revenue generation. The system connects **Asana**, **Notion**, **Airtable**, **Gmail**, and **Hugging Face** to orchestrate complex business workflows.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    MCP Orchestrator Layer                        │
│                  (src/mcp-orchestrator.js)                       │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│    Asana     │      │    Notion    │      │   Airtable   │
│   Projects   │      │  Databases   │      │    Tables    │
│    Tasks     │      │    Pages     │      │   Records    │
└──────────────┘      └──────────────┘      └──────────────┘
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│    Gmail     │      │ Hugging Face │      │   External   │
│   Alerts     │      │   AI Models  │      │   Services   │
└──────────────┘      └──────────────┘      └──────────────┘
```

## Key Features

### 🔄 Automated Workflows

1. **SEO Ranking Drop Response**
   - Detects ranking drops via RankYak
   - Logs event in Airtable
   - Creates urgent task in Asana
   - Updates Notion dashboard
   - Sends email alert via Gmail

2. **High-Performing Content Amplification**
   - Monitors MailChimp CTR
   - Stores metrics in Airtable
   - Creates amplification task in Asana
   - Logs in Notion
   - Notifies team via Gmail

3. **Crisis Event Response**
   - Monitors GDELT via Tax Collector
   - Creates crisis page in Notion
   - Generates urgent task in Asana
   - Tracks in Airtable
   - Sends immediate alert via Gmail

4. **B2B Client Onboarding**
   - Triggered by PayPal payment
   - Creates client record in Airtable
   - Builds client page in Notion
   - Generates onboarding tasks in Asana
   - Sends welcome email via Gmail

5. **Weekly Performance Report**
   - Aggregates metrics from Airtable
   - Creates report in Notion
   - Sends via Gmail
   - Creates follow-up tasks in Asana

### 🎯 MCP Server Integrations

#### Asana
- **Purpose**: Project management and task orchestration
- **Tools Used**:
  - `asana_list_workspaces` - Get workspaces
  - `asana_create_project` - Create workflow projects
  - `asana_create_task` - Generate automated tasks
  - `asana_update_task` - Update task status
  - `asana_typeahead_search` - Search for items

#### Notion
- **Purpose**: Operational command center and documentation
- **Tools Used**:
  - `search_notion` - Search workspace
  - `create_page` - Create documentation pages
  - `create_database` - Build tracking databases
  - `create_database_item` - Add records
  - `query_database` - Retrieve data

#### Airtable
- **Purpose**: Structured data tracking and analytics
- **Tools Used**:
  - `list_bases` - Get available bases
  - `list_tables` - Get tables in base
  - `create_records` - Add new data
  - `list_records` - Query data
  - `update_records` - Modify existing data

#### Gmail
- **Purpose**: Email automation and notifications
- **Tools Used**:
  - `send_email` - Send automated emails
  - `list_labels` - Organize emails
  - `search_emails` - Find messages

#### Hugging Face
- **Purpose**: AI model discovery and deployment
- **Tools Used**:
  - `model_search` - Find AI models
  - `dataset_search` - Discover datasets
  - `hub_repo_details` - Get model info
  - `gr1_qwen_image_fast_generate_image` - Generate images

## Installation & Setup

### Prerequisites

- Node.js 18+
- `manus-mcp-cli` installed and configured
- MCP servers authenticated (Asana, Notion, Airtable, Gmail, Hugging Face)

### Quick Start

1. **Clone the repository**
   ```bash
   cd ~/The-lab-verse-monitoring-
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Configure environment**
   ```bash
   cp .env.mcp .env.mcp.local
   # Edit .env.mcp.local with your actual values
   ```

4. **Run setup wizard**
   ```bash
   ./launch-mcp-system.sh
   # Select option 3: Setup Wizard
   ```

5. **Verify setup**
   ```bash
   ./launch-mcp-system.sh
   # Select option 4: Run System Verification
   ```

6. **Launch system**
   ```bash
   ./launch-mcp-system.sh
   # Select option 1: Launch Full System
   ```

### Manual Configuration

If the setup wizard doesn't work, manually configure `.env.mcp`:

1. **Get Asana Workspace ID**
   ```bash
   manus-mcp-cli tool call asana_list_workspaces --server asana --input '{}'
   ```

2. **Create Asana Projects**
   ```bash
   # Content Pipeline
   manus-mcp-cli tool call asana_create_project --server asana --input '{
     "workspace": "YOUR_WORKSPACE_GID",
     "name": "Lab-Verse: Content Pipeline",
     "privacy_setting": "public_to_workspace"
   }'
   
   # SEO Recovery
   manus-mcp-cli tool call asana_create_project --server asana --input '{
     "workspace": "YOUR_WORKSPACE_GID",
     "name": "Lab-Verse: SEO Recovery",
     "privacy_setting": "public_to_workspace"
   }'
   
   # Crisis Response
   manus-mcp-cli tool call asana_create_project --server asana --input '{
     "workspace": "YOUR_WORKSPACE_GID",
     "name": "Lab-Verse: Crisis Response",
     "privacy_setting": "public_to_workspace"
   }'
   
   # Client Onboarding
   manus-mcp-cli tool call asana_create_project --server asana --input '{
     "workspace": "YOUR_WORKSPACE_GID",
     "name": "Lab-Verse: Client Onboarding",
     "privacy_setting": "public_to_workspace"
   }'
   ```

3. **Get Airtable Base ID**
   ```bash
   manus-mcp-cli tool call list_bases --server airtable --input '{}'
   ```

4. **Create Notion Databases** (Manual)
   - Go to your Notion workspace
   - Create databases with the schemas defined in `MCP_INTEGRATION_PLAN.md`
   - Copy database IDs from URLs

5. **Update `.env.mcp`** with all the IDs

## Usage

### Testing Individual Workflows

```bash
# Test SEO Ranking Drop workflow
./launch-mcp-system.sh
# Select option 2, then 1

# Test Content Amplification workflow
./launch-mcp-system.sh
# Select option 2, then 2

# Generate Weekly Report
./launch-mcp-system.sh
# Select option 2, then 5
```

### Programmatic Usage

```javascript
const MCPOrchestrator = require('./src/mcp-orchestrator.js');

const orchestrator = new MCPOrchestrator();

// Initialize
await orchestrator.initialize();

// Handle SEO ranking drop
await orchestrator.handleSEORankingDrop(
  'african trade policy',  // keyword
  3,                        // previous position
  8,                        // current position
  'https://example.com/article'
);

// Amplify high-performing content
await orchestrator.amplifyHighPerformingContent(
  'Breaking Trade News',    // title
  'https://example.com/news', // url
  0.18,                     // click rate (18%)
  250                       // total clicks
);

// Handle crisis event
await orchestrator.handleCrisisEvent(
  'Trade embargo announced', // description
  85,                        // urgency score
  ['South Africa', 'Nigeria'] // affected regions
);

// Onboard B2B client
await orchestrator.onboardB2BClient(
  'client@company.com',     // email
  'Acme Corp',              // name
  'Data Intelligence',      // product
  5000,                     // amount
  'TXN123456'              // transaction ID
);

// Generate weekly report
await orchestrator.generateWeeklyReport();
```

## Workflow Details

### Workflow 1: SEO Ranking Drop Response

**Trigger**: RankYak detects ranking drop > 5 positions

**Steps**:
1. Log event in Airtable `SEO Rankings` table
2. Create urgent task in Asana `SEO Recovery` project
3. Update Notion `System Metrics` database
4. Send email alert to stakeholders

**Expected Outcome**:
- Task created with 2-day deadline
- Team notified within 1 minute
- Dashboard updated in real-time

### Workflow 2: High-Performing Content Amplification

**Trigger**: MailChimp reports CTR > 15%

**Steps**:
1. Store metrics in Airtable `Content Performance` table
2. Create amplification task in Asana `Content Pipeline` project
3. Log in Notion `Content Performance` database
4. Send team notification

**Expected Outcome**:
- Content queued for social amplification
- Similar content creation task generated
- Performance tracked for analysis

### Workflow 3: Crisis Event Response

**Trigger**: Tax Collector detects GDELT urgency score > 75

**Steps**:
1. Create crisis page in Notion `Crisis Events` database
2. Generate urgent task in Asana `Crisis Response` project
3. Store in Airtable `Crisis Events` table
4. Send immediate alert to all stakeholders

**Expected Outcome**:
- Crisis validated within 30 minutes
- Content generated within 2 hours
- Published to WordPress within 4 hours

### Workflow 4: B2B Client Onboarding

**Trigger**: PayPal payment received webhook

**Steps**:
1. Create client record in Airtable `B2B Clients` table
2. Build client page in Notion `Clients` database
3. Generate 5 onboarding tasks in Asana
4. Send welcome email with next steps

**Expected Outcome**:
- Client onboarded within 24 hours
- First report delivered within 48 hours
- Onboarding call scheduled

### Workflow 5: Weekly Performance Report

**Trigger**: Scheduled (Monday 9 AM)

**Steps**:
1. Aggregate metrics from Airtable
2. Calculate KPIs (revenue, ROAS, CTR)
3. Create report in Notion
4. Send via Gmail to stakeholders
5. Create follow-up task in Asana

**Expected Outcome**:
- Comprehensive weekly report
- Actionable insights identified
- Next week's strategy planned

## Monitoring & Debugging

### Check MCP Server Status

```bash
# Test Asana connection
manus-mcp-cli tool list --server asana

# Test Notion connection
manus-mcp-cli tool list --server notion

# Test Airtable connection
manus-mcp-cli tool list --server airtable

# Test Gmail connection
manus-mcp-cli tool list --server gmail

# Test Hugging Face connection
manus-mcp-cli tool list --server hugging-face
```

### View Logs

```bash
# Check system logs
tail -f /tmp/launch-*.log

# Check Node.js logs
NODE_ENV=development node src/mcp-orchestrator.js
```

### Common Issues

1. **MCP server timeout**
   - Increase timeout in `callMCPTool()` function
   - Check MCP server authentication

2. **Missing environment variables**
   - Verify `.env.mcp` is loaded
   - Check all required IDs are configured

3. **Authentication errors**
   - Re-authenticate MCP servers
   - Check OAuth tokens are valid

## Performance Metrics

### Expected Response Times

- SEO Ranking Drop workflow: < 30 seconds
- Content Amplification workflow: < 20 seconds
- Crisis Event Response workflow: < 45 seconds
- B2B Client Onboarding workflow: < 60 seconds
- Weekly Report Generation: < 2 minutes

### System Capacity

- Concurrent workflows: 10+
- Daily task creation: 100+
- Weekly reports: Unlimited
- Email notifications: 500+/day

## Security

- All API keys stored in environment variables
- No credentials in code or Git
- MCP servers use OAuth authentication
- Email notifications use secure SMTP

## Roadmap

### Phase 1 (Current)
- ✅ Core MCP integrations
- ✅ 5 automated workflows
- ✅ Setup wizard
- ✅ Documentation

### Phase 2 (Next)
- ⏳ Hugging Face model integration
- ⏳ Image generation pipeline
- ⏳ Advanced analytics dashboard
- ⏳ Webhook receivers

### Phase 3 (Future)
- 📋 Machine learning predictions
- 📋 Natural language task creation
- 📋 Voice-activated workflows
- 📋 Mobile app integration

## Support

For issues or questions:

1. Check the [MCP Integration Plan](./MCP_INTEGRATION_PLAN.md)
2. Review [Workflow Summary](./workflow_summary.md)
3. Run system verification: `./launch-mcp-system.sh` → Option 4
4. Contact: deedk822@gmail.com

## License

Proprietary - The Lab-Verse Monitoring System

## Contributors

- System Architecture: The Lab-Verse Team
- MCP Integration: Manus AI Agent
- Documentation: Automated Generation

---

**Last Updated**: November 28, 2025
**Version**: 1.0.0
**Status**: Production Ready 🚀
