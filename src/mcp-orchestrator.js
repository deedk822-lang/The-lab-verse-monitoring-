/**
 * MCP Orchestrator - The Lab-Verse Monitoring System
 * 
 * This is the main orchestration layer that connects all MCP services
 * to create automated workflows for content intelligence and revenue generation.
 */

const { exec } = require('child_process');
const util = require('util');
const execPromise = util.promisify(exec);

class MCPOrchestrator {
  constructor() {
    this.asanaWorkspaceId = process.env.ASANA_WORKSPACE_ID;
    this.notionWorkspaceId = process.env.NOTION_WORKSPACE_ID;
    this.airtableBaseId = process.env.AIRTABLE_BASE_METRICS;
    this.gmailSender = process.env.GMAIL_SENDER_EMAIL || 'deedk822@gmail.com';
  }

  /**
   * Execute MCP tool call
   */
  async callMCPTool(server, toolName, input) {
    try {
      const inputJson = JSON.stringify(input);
      const command = `manus-mcp-cli tool call ${toolName} --server ${server} --input '${inputJson}'`;
      const { stdout, stderr } = await execPromise(command);
      
      if (stderr && !stderr.includes('Warning')) {
        console.error(`MCP Error (${server}/${toolName}):`, stderr);
      }
      
      return JSON.parse(stdout);
    } catch (error) {
      console.error(`Failed to call ${server}/${toolName}:`, error.message);
      throw error;
    }
  }

  /**
   * WORKFLOW 1: SEO Ranking Drop Response
   */
  async handleSEORankingDrop(keyword, previousPosition, currentPosition, url) {
    console.log(`🚨 SEO Alert: "${keyword}" dropped from #${previousPosition} to #${currentPosition}`);

    try {
      // 1. Log event in Airtable
      await this.callMCPTool('airtable', 'create_records', {
        base_id: this.airtableBaseId,
        table_id: process.env.AIRTABLE_TABLE_SEO_RANKINGS,
        records: [{
          fields: {
            'Keyword': keyword,
            'Previous Position': previousPosition,
            'Current Position': currentPosition,
            'Drop Amount': previousPosition - currentPosition,
            'URL': url,
            'Detected At': new Date().toISOString(),
            'Status': 'Needs Action'
          }
        }]
      });

      // 2. Create urgent task in Asana
      const task = await this.callMCPTool('asana', 'asana_create_task', {
        workspace: this.asanaWorkspaceId,
        name: `URGENT: Refresh "${keyword}" content`,
        notes: `Ranking dropped from #${previousPosition} to #${currentPosition}.\n\nURL: ${url}\n\nAction Required:\n1. Analyze competitor changes\n2. Update content\n3. Improve on-page SEO\n4. Add fresh data/insights`,
        due_on: this.getDateDaysFromNow(2),
        projects: [process.env.ASANA_PROJECT_SEO_RECOVERY]
      });

      // 3. Update Notion dashboard
      await this.callMCPTool('notion', 'create_database_item', {
        database_id: process.env.NOTION_DATABASE_METRICS,
        properties: {
          'Event Type': { select: { name: 'SEO Ranking Drop' } },
          'Keyword': { title: [{ text: { content: keyword } }] },
          'Severity': { select: { name: 'High' } },
          'Status': { select: { name: 'In Progress' } },
          'Asana Task': { url: task.permalink_url }
        }
      });

      // 4. Send alert email
      await this.callMCPTool('gmail', 'send_email', {
        to: process.env.GMAIL_STAKEHOLDER_LIST,
        subject: `🚨 SEO Alert: "${keyword}" ranking dropped`,
        body: `
          <h2>SEO Ranking Drop Detected</h2>
          <p><strong>Keyword:</strong> ${keyword}</p>
          <p><strong>Previous Position:</strong> #${previousPosition}</p>
          <p><strong>Current Position:</strong> #${currentPosition}</p>
          <p><strong>Drop:</strong> ${previousPosition - currentPosition} positions</p>
          <p><strong>URL:</strong> <a href="${url}">${url}</a></p>
          <p><strong>Action:</strong> Task created in Asana for immediate content refresh</p>
        `
      });

      console.log('✅ SEO ranking drop workflow completed');
      return { success: true, taskId: task.gid };
    } catch (error) {
      console.error('❌ SEO ranking drop workflow failed:', error);
      throw error;
    }
  }

  /**
   * WORKFLOW 2: High-Performing Content Amplification
   * Triggered when MailChimp reports high CTR
   */
  async amplifyHighPerformingContent(contentTitle, contentUrl, clickRate, totalClicks) {
    console.log(`📊 High Performance: "${contentTitle}" - ${(clickRate * 100).toFixed(1)}% CTR`);

    try {
      // 1. Store metrics in Airtable
      await this.callMCPTool('airtable', 'create_records', {
        base_id: this.airtableBaseId,
        table_id: process.env.AIRTABLE_TABLE_CONTENT_PERFORMANCE,
        records: [{
          fields: {
            'Title': contentTitle,
            'URL': contentUrl,
            'Email CTR': clickRate,
            'Total Clicks': totalClicks,
            'Date': new Date().toISOString(),
            'Amplification Status': 'Queued'
          }
        }]
      });

      // 2. Create amplification task in Asana
      await this.callMCPTool('asana', 'asana_create_task', {
        workspace: this.asanaWorkspaceId,
        name: `Amplify: ${contentTitle}`,
        notes: `This content is performing exceptionally well!\n\nEmail CTR: ${(clickRate * 100).toFixed(1)}%\nTotal Clicks: ${totalClicks}\n\nActions:\n1. Share on LinkedIn, Twitter, Facebook\n2. Create similar content\n3. Analyze what made it successful`,
        due_on: this.getDateDaysFromNow(1),
        projects: [process.env.ASANA_PROJECT_CONTENT_PIPELINE]
      });

      // 3. Log in Notion
      await this.callMCPTool('notion', 'create_database_item', {
        database_id: process.env.NOTION_DATABASE_CONTENT,
        properties: {
          'Title': { title: [{ text: { content: contentTitle } }] },
          'URL': { url: contentUrl },
          'Email CTR': { number: clickRate },
          'Status': { select: { name: 'High Performer' } },
          'Action': { select: { name: 'Amplify' } }
        }
      });

      // 4. Send team notification
      await this.callMCPTool('gmail', 'send_email', {
        to: process.env.GMAIL_STAKEHOLDER_LIST,
        subject: `📊 High-Performing Content: ${contentTitle}`,
        body: `
          <h2>Content Performance Alert</h2>
          <p><strong>Title:</strong> ${contentTitle}</p>
          <p><strong>Email CTR:</strong> ${(clickRate * 100).toFixed(1)}%</p>
          <p><strong>Total Clicks:</strong> ${totalClicks}</p>
          <p><strong>URL:</strong> <a href="${contentUrl}">${contentUrl}</a></p>
          <p><strong>Next Steps:</strong> Amplify via social media and create similar content</p>
        `
      });

      console.log('✅ Content amplification workflow completed');
      return { success: true };
    } catch (error) {
      console.error('❌ Content amplification workflow failed:', error);
      throw error;
    }
  }

  /**
   * WORKFLOW 3: Crisis Event Response
   * Triggered by Tax Collector (GDELT monitoring)
   */
  async handleCrisisEvent(crisisDescription, urgencyScore, affectedRegions) {
    console.log(`🚨 Crisis Detected: ${crisisDescription} (Urgency: ${urgencyScore})`);

    try {
      // 1. Log in Notion
      const notionPage = await this.callMCPTool('notion', 'create_page', {
        parent_database_id: process.env.NOTION_DATABASE_CRISIS_EVENTS,
        properties: {
          'Crisis': { title: [{ text: { content: crisisDescription } }] },
          'Urgency Score': { number: urgencyScore },
          'Regions': { multi_select: affectedRegions.map(r => ({ name: r })) },
          'Status': { select: { name: 'Detected' } }
        }
      });

      // 2. Create urgent response task in Asana
      await this.callMCPTool('asana', 'asana_create_task', {
        workspace: this.asanaWorkspaceId,
        name: `CRISIS: ${crisisDescription}`,
        notes: `Urgency Score: ${urgencyScore}/100\nAffected Regions: ${affectedRegions.join(', ')}\n\nActions:\n1. Validate with NewsAPI\n2. Run through Judge System\n3. Generate Guardian Engine content\n4. Publish to WordPress\n5. Track performance`,
        due_on: this.getDateDaysFromNow(0), // Due today
        projects: [process.env.ASANA_PROJECT_CRISIS_RESPONSE]
      });

      // 3. Store in Airtable for tracking
      await this.callMCPTool('airtable', 'create_records', {
        base_id: this.airtableBaseId,
        table_id: process.env.AIRTABLE_TABLE_CRISIS_EVENTS,
        records: [{
          fields: {
            'Description': crisisDescription,
            'Urgency Score': urgencyScore,
            'Regions': affectedRegions.join(', '),
            'Detected At': new Date().toISOString(),
            'Status': 'Validating'
          }
        }]
      });

      // 4. Send immediate alert
      await this.callMCPTool('gmail', 'send_email', {
        to: process.env.GMAIL_STAKEHOLDER_LIST,
        subject: `🚨 CRISIS ALERT: ${crisisDescription}`,
        body: `
          <h2 style="color: red;">Crisis Event Detected</h2>
          <p><strong>Description:</strong> ${crisisDescription}</p>
          <p><strong>Urgency Score:</strong> ${urgencyScore}/100</p>
          <p><strong>Affected Regions:</strong> ${affectedRegions.join(', ')}</p>
          <p><strong>Status:</strong> Validation in progress</p>
          <p><strong>Next Steps:</strong> Content generation and publication workflow initiated</p>
        `
      });

      console.log('✅ Crisis event response workflow initiated');
      return { success: true, notionPageId: notionPage.id };
    } catch (error) {
      console.error('❌ Crisis event response workflow failed:', error);
      throw error;
    }
  }

  /**
   * WORKFLOW 4: B2B Client Onboarding
   * Triggered when PayPal payment is received
   */
  async onboardB2BClient(clientEmail, clientName, productName, amount, transactionId) {
    console.log(`💰 New Client: ${clientName} - ${productName} ($${amount})`);

    try {
      // 1. Create client record in Airtable
      await this.callMCPTool('airtable', 'create_records', {
        base_id: process.env.AIRTABLE_BASE_CLIENTS,
        table_id: process.env.AIRTABLE_TABLE_B2B_CLIENTS,
        records: [{
          fields: {
            'Client Name': clientName,
            'Email': clientEmail,
            'Product': productName,
            'Amount': amount,
            'Transaction ID': transactionId,
            'Status': 'Active',
            'Onboarded At': new Date().toISOString()
          }
        }]
      });

      // 2. Create client page in Notion
      await this.callMCPTool('notion', 'create_page', {
        parent_database_id: process.env.NOTION_DATABASE_CLIENTS,
        properties: {
          'Client Name': { title: [{ text: { content: clientName } }] },
          'Email': { email: clientEmail },
          'Product': { select: { name: productName } },
          'Status': { select: { name: 'Active' } },
          'Revenue': { number: amount }
        }
      });

      // 3. Create onboarding tasks in Asana
      const onboardingTasks = [
        'Send welcome email with credentials',
        'Schedule onboarding call',
        'Set up Grafana dashboard access',
        'Configure data delivery pipeline',
        'Send first intelligence report'
      ];

      for (const taskName of onboardingTasks) {
        await this.callMCPTool('asana', 'asana_create_task', {
          workspace: this.asanaWorkspaceId,
          name: `${clientName}: ${taskName}`,
          projects: [process.env.ASANA_PROJECT_CLIENT_ONBOARDING]
        });
      }

      // 4. Send welcome email
      await this.callMCPTool('gmail', 'send_email', {
        to: clientEmail,
        subject: `Welcome to The Lab-Verse Intelligence Platform!`,
        body: `
          <h2>Welcome, ${clientName}!</h2>
          <p>Thank you for subscribing to <strong>${productName}</strong>.</p>
          <p><strong>Transaction ID:</strong> ${transactionId}</p>
          <p><strong>Amount:</strong> $${amount}</p>
          <h3>What's Next?</h3>
          <ul>
            <li>You'll receive your access credentials within 24 hours</li>
            <li>Our team will schedule an onboarding call</li>
            <li>Your first intelligence report will be delivered within 48 hours</li>
          </ul>
          <p>If you have any questions, reply to this email.</p>
          <p>Best regards,<br>The Lab-Verse Team</p>
        `
      });

      console.log('✅ B2B client onboarding workflow completed');
      return { success: true };
    } catch (error) {
      console.error('❌ B2B client onboarding workflow failed:', error);
      throw error;
    }
  }

  /**
   * WORKFLOW 5: Weekly Performance Report
   * Scheduled to run every Monday
   */
  async generateWeeklyReport() {
    console.log('📊 Generating weekly performance report...');

    try {
      // 1. Aggregate metrics from Airtable
      const contentPerformance = await this.callMCPTool('airtable', 'list_records', {
        base_id: this.airtableBaseId,
        table_id: process.env.AIRTABLE_TABLE_CONTENT_PERFORMANCE,
        filter_by_formula: `IS_AFTER({Date}, DATEADD(TODAY(), -7, 'days'))`
      });

      const adCampaigns = await this.callMCPTool('airtable', 'list_records', {
        base_id: this.airtableBaseId,
        table_id: process.env.AIRTABLE_TABLE_AD_CAMPAIGNS,
        filter_by_formula: `IS_AFTER({Date}, DATEADD(TODAY(), -7, 'days'))`
      });

      // 2. Calculate key metrics
      const totalRevenue = adCampaigns.records.reduce((sum, r) => sum + (r.fields['Revenue'] || 0), 0);
      const totalSpend = adCampaigns.records.reduce((sum, r) => sum + (r.fields['Spend'] || 0), 0);
      const roas = totalSpend > 0 ? (totalRevenue / totalSpend).toFixed(2) : 0;
      const avgCTR = contentPerformance.records.reduce((sum, r) => sum + (r.fields['Email CTR'] || 0), 0) / contentPerformance.records.length;

      // 3. Create report in Notion
      const reportContent = `
# Weekly Performance Report - ${new Date().toLocaleDateString()}

## Revenue Metrics
- **Total Revenue**: $${totalRevenue.toFixed(2)}
- **Total Ad Spend**: $${totalSpend.toFixed(2)}
- **ROAS**: ${roas}:1

## Content Performance
- **Articles Published**: ${contentPerformance.records.length}
- **Average Email CTR**: ${(avgCTR * 100).toFixed(2)}%

## Top Performing Content
${contentPerformance.records.slice(0, 5).map((r, i) => 
  `${i + 1}. ${r.fields['Title']} - ${(r.fields['Email CTR'] * 100).toFixed(1)}% CTR`
).join('\n')}
      `;

      await this.callMCPTool('notion', 'create_page', {
        parent_page_id: process.env.NOTION_PAGE_REPORTS,
        title: `Weekly Report - ${new Date().toLocaleDateString()}`,
        content: reportContent
      });

      // 4. Send report via email
      await this.callMCPTool('gmail', 'send_email', {
        to: process.env.GMAIL_STAKEHOLDER_LIST,
        subject: `📊 Weekly Performance Report - ${new Date().toLocaleDateString()}`,
        body: reportContent.replace(/\n/g, '<br>').replace(/##/g, '<h3>').replace(/#/g, '<h2>')
      });

      // 5. Create follow-up tasks in Asana
      await this.callMCPTool('asana', 'asana_create_task', {
        workspace: this.asanaWorkspaceId,
        name: `Review weekly performance and plan next week`,
        notes: `ROAS: ${roas}:1\nAvg CTR: ${(avgCTR * 100).toFixed(2)}%\n\nReview the report and plan content strategy for next week.`,
        projects: [process.env.ASANA_PROJECT_CONTENT_PIPELINE]
      });

      console.log('✅ Weekly performance report generated');
      return { success: true, totalRevenue, roas };
    } catch (error) {
      console.error('❌ Weekly performance report failed:', error);
      throw error;
    }
  }

  /**
   * Helper: Get date N days from now
   */
  getDateDaysFromNow(days) {
    const date = new Date();
    date.setDate(date.getDate() + days);
    return date.toISOString().split('T')[0];
  }

  /**
   * Initialize the orchestrator
   */
  async initialize() {
    console.log('🚀 Initializing MCP Orchestrator...');
    
    // Verify environment variables
    const required = [
      'ASANA_WORKSPACE_ID',
      'NOTION_WORKSPACE_ID',
      'AIRTABLE_BASE_METRICS',
      'GMAIL_SENDER_EMAIL'
    ];

    const missing = required.filter(key => !process.env[key]);
    if (missing.length > 0) {
      throw new Error(`Missing required environment variables: ${missing.join(', ')}`);
    }

    console.log('✅ MCP Orchestrator initialized successfully');
  }
}

module.exports = MCPOrchestrator;

// CLI usage
if (require.main === module) {
  const orchestrator = new MCPOrchestrator();
  
  orchestrator.initialize()
    .then(() => {
      console.log('MCP Orchestrator is ready!');
      console.log('Available workflows:');
      console.log('  1. handleSEORankingDrop()');
      console.log('  2. amplifyHighPerformingContent()');
      console.log('  3. handleCrisisEvent()');
      console.log('  4. onboardB2BClient()');
      console.log('  5. generateWeeklyReport()');
    })
    .catch(error => {
      console.error('Failed to initialize:', error);
      process.exit(1);
    });
}
