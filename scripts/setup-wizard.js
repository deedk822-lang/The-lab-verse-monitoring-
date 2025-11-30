#!/usr/bin/env node

/**
 * Setup Wizard for The Lab-Verse Monitoring System
 * 
 * This interactive wizard helps configure Notion, Asana, and Airtable
 * for the workflow automation system.
 */

const { exec } = require('child_process');
const util = require('util');
const fs = require('fs').promises;
const path = require('path');
const readline = require('readline');

const execPromise = util.promisify(exec);

// Colors for console output
const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  magenta: '\x1b[35m',
  cyan: '\x1b[36m',
};

// Helper to create readline interface
const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

// Promisified question
const question = (query) => new Promise((resolve) => rl.question(query, resolve));

// Log functions
const log = {
  info: (msg) => console.log(`${colors.blue}[INFO]${colors.reset} ${msg}`),
  success: (msg) => console.log(`${colors.green}[SUCCESS]${colors.reset} ${msg}`),
  warning: (msg) => console.log(`${colors.yellow}[WARNING]${colors.reset} ${msg}`),
  error: (msg) => console.log(`${colors.red}[ERROR]${colors.reset} ${msg}`),
  header: (msg) => console.log(`\n${colors.bright}${colors.cyan}${msg}${colors.reset}\n`),
};

// MCP tool caller
async function callMCPTool(server, toolName, input) {
  try {
    const inputJson = JSON.stringify(input).replace(/'/g, "'\\''");
    const command = `manus-mcp-cli tool call ${toolName} --server ${server} --input '${inputJson}'`;
    const { stdout, stderr } = await execPromise(command, { timeout: 30000 });
    
    if (stderr && !stderr.includes('Warning')) {
      log.warning(`MCP stderr: ${stderr}`);
    }
    
    return JSON.parse(stdout);
  } catch (error) {
    throw new Error(`MCP call failed: ${error.message}`);
  }
}

// Configuration storage
let config = {
  asana: {},
  notion: {},
  airtable: {},
  gmail: {}
};

// Main setup wizard
async function runSetupWizard() {
  console.clear();
  log.header('═══════════════════════════════════════════════════════════════');
  log.header('  The Lab-Verse Monitoring System - Setup Wizard');
  log.header('═══════════════════════════════════════════════════════════════');
  
  console.log('This wizard will help you configure:');
  console.log('  1. Asana - Project management');
  console.log('  2. Notion - Operational command center');
  console.log('  3. Airtable - Data tracking');
  console.log('  4. Gmail - Email automation\n');
  
  const proceed = await question('Continue with setup? (y/n): ');
  if (proceed.toLowerCase() !== 'y') {
    log.info('Setup cancelled');
    rl.close();
    return;
  }

  try {
    // Step 1: Configure Asana
    await setupAsana();
    
    // Step 2: Configure Notion
    await setupNotion();
    
    // Step 3: Configure Airtable
    await setupAirtable();
    
    // Step 4: Configure Gmail
    await setupGmail();
    
    // Step 5: Save configuration
    await saveConfiguration();
    
    // Step 6: Verify setup
    await verifySetup();
    
    log.success('\n✅ Setup completed successfully!');
    log.info('\nNext steps:');
    log.info('  1. Review the generated .env.mcp file');
    log.info('  2. Run: ./launch-mcp-system.sh');
    log.info('  3. Select option 4 to verify system');
    
  } catch (error) {
    log.error(`Setup failed: ${error.message}`);
    process.exit(1);
  } finally {
    rl.close();
  }
}

// Setup Asana
async function setupAsana() {
  log.header('Step 1: Asana Configuration');
  
  try {
    log.info('Fetching your Asana workspaces...');
    const workspaces = await callMCPTool('asana', 'asana_list_workspaces', {});
    
    if (!workspaces.data || workspaces.data.length === 0) {
      log.warning('No Asana workspaces found. Please ensure you are authenticated.');
      return;
    }
    
    console.log('\nAvailable workspaces:');
    workspaces.data.forEach((ws, idx) => {
      console.log(`  ${idx + 1}. ${ws.name} (${ws.gid})`);
    });
    
    const wsChoice = await question('\nSelect workspace (enter number): ');
    const selectedWs = workspaces.data[parseInt(wsChoice) - 1];
    
    if (!selectedWs) {
      throw new Error('Invalid workspace selection');
    }
    
    config.asana.workspace_id = selectedWs.gid;
    log.success(`Selected workspace: ${selectedWs.name}`);
    
    // Create projects
    log.info('\nCreating Asana projects for workflows...');
    
    const projects = [
      { name: 'Content Pipeline', notes: 'Content creation and distribution workflow' },
      { name: 'SEO Recovery', notes: 'SEO ranking drop response and content refresh' },
      { name: 'Crisis Response', notes: 'Crisis event monitoring and content generation' },
      { name: 'Client Onboarding', notes: 'B2B client onboarding and management' }
    ];
    
    for (const project of projects) {
      try {
        const created = await callMCPTool('asana', 'asana_create_project', {
          workspace: selectedWs.gid,
          name: `Lab-Verse: ${project.name}`,
          notes: project.notes,
          privacy_setting: 'public_to_workspace'
        });
        
        const projectKey = project.name.toLowerCase().replace(/ /g, '_');
        config.asana[`project_${projectKey}`] = created.data.gid;
        log.success(`Created project: ${project.name}`);
      } catch (error) {
        log.warning(`Failed to create project ${project.name}: ${error.message}`);
      }
    }
    
  } catch (error) {
    log.error(`Asana setup failed: ${error.message}`);
    throw error;
  }
}

// Setup Notion
async function setupNotion() {
  log.header('Step 2: Notion Configuration');
  
  try {
    log.info('Searching for Notion workspace...');
    
    // Try to search for existing pages
    const searchResult = await callMCPTool('notion', 'search_notion', {
      query: '',
      page_size: 1
    });
    
    if (searchResult.results && searchResult.results.length > 0) {
      log.success('Notion connection verified');
      
      // Create operational command center
      log.info('\nCreating Notion databases...');
      
      const databases = [
        {
          name: 'Revenue Operations',
          properties: {
            'Client Name': { type: 'title' },
            'Email': { type: 'email' },
            'Product': { type: 'select', options: ['Data Intelligence', 'Predictive Reports', 'Compliance'] },
            'Revenue': { type: 'number', format: 'dollar' },
            'Status': { type: 'select', options: ['Active', 'Churned', 'Pending'] }
          }
        },
        {
          name: 'Content Performance',
          properties: {
            'Title': { type: 'title' },
            'URL': { type: 'url' },
            'Email CTR': { type: 'number', format: 'percent' },
            'Status': { type: 'select', options: ['Published', 'High Performer', 'Needs Refresh'] },
            'Action': { type: 'select', options: ['None', 'Amplify', 'Update', 'Archive'] }
          }
        },
        {
          name: 'System Metrics',
          properties: {
            'Event Type': { type: 'select', options: ['SEO Ranking Drop', 'High Performance', 'Crisis', 'Revenue'] },
            'Keyword': { type: 'title' },
            'Severity': { type: 'select', options: ['Low', 'Medium', 'High', 'Critical'] },
            'Status': { type: 'select', options: ['Detected', 'In Progress', 'Resolved'] },
            'Asana Task': { type: 'url' }
          }
        },
        {
          name: 'Crisis Events',
          properties: {
            'Crisis': { type: 'title' },
            'Urgency Score': { type: 'number' },
            'Regions': { type: 'multi_select' },
            'Status': { type: 'select', options: ['Detected', 'Validating', 'Publishing', 'Published'] }
          }
        }
      ];
      
      for (const db of databases) {
        try {
          // Note: create_database requires parent page, which we'll skip for now
          log.info(`Database schema prepared: ${db.name}`);
          log.info('  Please create these databases manually in Notion and update .env.mcp');
        } catch (error) {
          log.warning(`Database ${db.name}: ${error.message}`);
        }
      }
      
      log.info('\nNotion setup requires manual database creation.');
      log.info('Please create the databases listed above in your Notion workspace.');
      
    } else {
      log.warning('Could not verify Notion connection');
    }
    
  } catch (error) {
    log.error(`Notion setup failed: ${error.message}`);
    log.info('You may need to authenticate Notion MCP server first');
  }
}

// Setup Airtable
async function setupAirtable() {
  log.header('Step 3: Airtable Configuration');
  
  try {
    log.info('Fetching your Airtable bases...');
    const bases = await callMCPTool('airtable', 'list_bases', {});
    
    if (!bases.bases || bases.bases.length === 0) {
      log.warning('No Airtable bases found. Please create a base first.');
      return;
    }
    
    console.log('\nAvailable bases:');
    bases.bases.forEach((base, idx) => {
      console.log(`  ${idx + 1}. ${base.name} (${base.id})`);
    });
    
    const baseChoice = await question('\nSelect base for metrics (enter number): ');
    const selectedBase = bases.bases[parseInt(baseChoice) - 1];
    
    if (!selectedBase) {
      throw new Error('Invalid base selection');
    }
    
    config.airtable.base_metrics = selectedBase.id;
    log.success(`Selected base: ${selectedBase.name}`);
    
    // List tables in the base
    log.info('\nFetching tables in base...');
    const tables = await callMCPTool('airtable', 'list_tables', {
      base_id: selectedBase.id
    });
    
    if (tables.tables && tables.tables.length > 0) {
      console.log('\nExisting tables:');
      tables.tables.forEach((table, idx) => {
        console.log(`  ${idx + 1}. ${table.name} (${table.id})`);
      });
      
      log.info('\nYou can use these tables or create new ones for:');
      log.info('  - Content Performance');
      log.info('  - Ad Campaigns');
      log.info('  - SEO Rankings');
      log.info('  - Crisis Events');
      log.info('  - B2B Clients');
    }
    
  } catch (error) {
    log.error(`Airtable setup failed: ${error.message}`);
    throw error;
  }
}

// Setup Gmail
async function setupGmail() {
  log.header('Step 4: Gmail Configuration');
  
  try {
    log.info('Verifying Gmail connection...');
    
    // Try to list labels to verify connection
    const labels = await callMCPTool('gmail', 'list_labels', {});
    
    if (labels.labels && labels.labels.length > 0) {
      log.success('Gmail connection verified');
      log.info(`Found ${labels.labels.length} labels in your account`);
      
      config.gmail.sender_email = 'deedk822@gmail.com';
      log.success('Gmail configured for automated emails');
    } else {
      log.warning('Could not verify Gmail connection');
    }
    
  } catch (error) {
    log.error(`Gmail setup failed: ${error.message}`);
    log.info('You may need to authenticate Gmail MCP server first');
  }
}

// Save configuration to .env.mcp
async function saveConfiguration() {
  log.header('Saving Configuration');
  
  const envPath = path.join(process.cwd(), '.env.mcp');
  
  try {
    // Read existing .env.mcp
    let envContent = await fs.readFile(envPath, 'utf-8');
    
    // Update values
    if (config.asana.workspace_id) {
      envContent = envContent.replace(
        /ASANA_WORKSPACE_ID=.*/,
        `ASANA_WORKSPACE_ID=${config.asana.workspace_id}`
      );
    }
    
    if (config.asana.project_content_pipeline) {
      envContent = envContent.replace(
        /ASANA_PROJECT_CONTENT_PIPELINE=.*/,
        `ASANA_PROJECT_CONTENT_PIPELINE=${config.asana.project_content_pipeline}`
      );
    }
    
    if (config.asana.project_seo_recovery) {
      envContent = envContent.replace(
        /ASANA_PROJECT_SEO_RECOVERY=.*/,
        `ASANA_PROJECT_SEO_RECOVERY=${config.asana.project_seo_recovery}`
      );
    }
    
    if (config.asana.project_crisis_response) {
      envContent = envContent.replace(
        /ASANA_PROJECT_CRISIS_RESPONSE=.*/,
        `ASANA_PROJECT_CRISIS_RESPONSE=${config.asana.project_crisis_response}`
      );
    }
    
    if (config.asana.project_client_onboarding) {
      envContent = envContent.replace(
        /ASANA_PROJECT_CLIENT_ONBOARDING=.*/,
        `ASANA_PROJECT_CLIENT_ONBOARDING=${config.asana.project_client_onboarding}`
      );
    }
    
    if (config.airtable.base_metrics) {
      envContent = envContent.replace(
        /AIRTABLE_BASE_METRICS=.*/,
        `AIRTABLE_BASE_METRICS=${config.airtable.base_metrics}`
      );
    }
    
    // Write updated content
    await fs.writeFile(envPath, envContent);
    log.success('Configuration saved to .env.mcp');
    
    // Display summary
    console.log('\n' + '='.repeat(70));
    console.log('Configuration Summary:');
    console.log('='.repeat(70));
    console.log(JSON.stringify(config, null, 2));
    console.log('='.repeat(70));
    
  } catch (error) {
    log.error(`Failed to save configuration: ${error.message}`);
    throw error;
  }
}

// Verify setup
async function verifySetup() {
  log.header('Verifying Setup');
  
  const checks = [];
  
  // Check Asana
  if (config.asana.workspace_id) {
    checks.push({ name: 'Asana Workspace', status: '✅' });
  } else {
    checks.push({ name: 'Asana Workspace', status: '❌' });
  }
  
  // Check Notion
  checks.push({ name: 'Notion Connection', status: '⚠️  Manual setup required' });
  
  // Check Airtable
  if (config.airtable.base_metrics) {
    checks.push({ name: 'Airtable Base', status: '✅' });
  } else {
    checks.push({ name: 'Airtable Base', status: '❌' });
  }
  
  // Check Gmail
  if (config.gmail.sender_email) {
    checks.push({ name: 'Gmail Connection', status: '✅' });
  } else {
    checks.push({ name: 'Gmail Connection', status: '❌' });
  }
  
  console.log('\nSetup Verification:');
  checks.forEach(check => {
    console.log(`  ${check.status} ${check.name}`);
  });
}

// Run the wizard
runSetupWizard().catch(error => {
  log.error(`Fatal error: ${error.message}`);
  process.exit(1);
});
