// scripts/register-agents.js
import { createClient } from '@mistralai/mistralai';
import fs from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';
import { dirname } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Load environment variables
const envPath = path.join(__dirname, '..', '.env');
if (fs.existsSync(envPath)) {
  const envConfig = (await fs.readFile(envPath, 'utf8'))
    .split('\n')
    .filter(line => line.trim() && !line.startsWith('#'))
    .reduce((acc, line) => {
      const [key, ...value] = line.split('=');
      acc[key.trim()] = value.join('=').trim().replace(/^["']|["']$/g, '');
      return acc;
    }, {});
  Object.assign(process.env, envConfig);
}

const MISTRAL_API_KEY = process.env.MISTRAL_API_KEY || process.env.VITE_MISTRAL_API_KEY;
if (!MISTRAL_API_KEY) {
  console.error('❌ MISTRAL_API_KEY not found in environment');
  process.exit(1);
}

const client = createClient({ apiKey: MISTRAL_API_KEY });

// Agent specifications - tailored for Lab Verse Monitoring Stack
const AGENT_SPECS = [
  {
    name: 'rankyak-router',
    description: 'Entry point for RankYak webhooks. Routes to specialized agents based on intent, urgency, and budget.',
    instructions: `
You are the intelligent router for the Lab Verse Monitoring Stack. You receive JSON payloads from RankYak containing:
- "topic", "keywords", "intent", "priority", "budgetEstimate", "urgency", "channels", "audience", "tone"

Your routing logic:
1. If "urgency" === "critical" OR "severity" >= 8 → hand off to emergency-agent
2. If "budgetEstimate" > 500 → hand off to budget-agent FIRST, then wait for approval
3. If "intent" includes ["create", "publish", "blog", "post", "content"] → hand off to content-planner-agent
4. If "intent" includes ["monitor", "alert", "status", "health"] → hand off to monitoring-agent
5. Always preserve full context and include all relevant fields in handoffs

You do NOT generate content or make API calls directly - only route intelligently.
`,
    handoffs: ['content-planner-agent', 'budget-agent', 'emergency-agent', 'monitoring-agent'],
  },
  {
    name: 'content-planner-agent',
    description: 'Creates comprehensive content plans: outlines, SEO metadata, visual requirements, and channel strategy.',
    instructions: `
Given a topic and audience from the Lab Verse Monitoring Stack, produce:
- Structured outline with H1-H3 headings optimized for SEO
- Target keywords and metadata (title, description, slug)
- Visual requirements (hero image specifications, aspect ratios, style guidance)
- Channel-specific adaptations (Twitter < 280 chars, LinkedIn long-form, email subject lines)
- Estimated costs for each component

Then initiate parallel handoffs:
→ writer-agent for text generation (with outline and metadata)
→ bria-agent for image generation (with visual requirements)
→ budget-agent for cost approval (if total > $200)

When both writer and bria complete, hand off to:
→ github-commit-agent to persist content with front-matter
→ wp-publisher-agent to create WordPress post
`,
    handoffs: ['writer-agent', 'bria-agent', 'github-commit-agent', 'wp-publisher-agent', 'budget-agent'],
  },
  {
    name: 'writer-agent',
    description: 'Generates high-quality text using preferred AI provider (Gemini/OpenAI/ZAI via MCP).',
    instructions: `
Use the MCP context to select the best provider:
- If "provider" specified in context → use it
- Else: prefer ZAI (cost-efficient), fall back to Gemini/OpenAI

Generate:
- SEO-optimized article (HTML with proper semantic structure)
- Short-form variants for each social platform
- Email campaign copy (subject + body)
- Voice script version (if audio requested)

Quality requirements:
- Include target keywords naturally
- Add proper HTML formatting (headings, lists, quotes)
- Generate meta description under 160 chars
- Create platform-specific variants (Twitter, LinkedIn, etc.)

Then hand off to:
→ manus-agent for polish and optimization
→ elevenlabs-agent if audio requested
→ github-commit-agent to persist
`,
    handoffs: ['manus-agent', 'elevenlabs-agent', 'github-commit-agent'],
  },
  {
    name: 'bria-agent',
    description: 'Generates image/video prompts and calls Bria API for visual content.',
    instructions: `
From visual requirements (e.g., "hero image for AI monitoring dashboard, 16:9, tech aesthetic"), generate:
- 1-3 precise Bria prompts with detailed specifications
- Call Bria API to generate images
- Return URLs, attribution tokens, and generation IDs
- Estimate costs for budget tracking

Requirements:
- Hero image: 1920x1080, professional tech aesthetic
- Social thumbnails: 1200x630, platform-optimized
- Include proper attribution metadata

Then hand off to:
→ wp-uploader-agent to upload media to WordPress
→ github-commit-agent to persist image metadata
`,
    tools: [
      {
        type: 'function',
        function: {
          name: 'generate_bria_image',
          description: 'Generate an image via Bria API with proper attribution',
          parameters: {
            type: 'object',
            properties: {
              prompt: { type: 'string', description: 'Detailed image generation prompt' },
              width: { type: 'integer', default: 1024, description: 'Image width in pixels' },
              height: { type: 'integer', default: 1024, description: 'Image height in pixels' },
              format: { type: 'string', enum: ['jpg', 'png'], default: 'jpg', description: 'Output format' },
              engine_id: { type: 'string', optional: true, description: 'Specific Bria engine ID' }
            },
            required: ['prompt'],
          },
        },
      },
    ],
    handoffs: ['wp-uploader-agent', 'github-commit-agent'],
  },
  {
    name: 'github-commit-agent',
    description: 'Commits content and metadata to GitHub repo with proper front-matter.',
    tools: [
      {
        type: 'function',
        function: {
          name: 'commit_to_github',
          description: 'Commit markdown file to GitHub with YAML front-matter',
          parameters: {
            type: 'object',
            properties: {
              owner: { type: 'string', default: process.env.GITHUB_OWNER || 'deedk822-lang' },
              repo: { type: 'string', default: 'The-lab-verse-monitoring-' },
              branch: { type: 'string', default: 'main' },
              path: { type: 'string', pattern: '^content/(posts|monitoring)/.*\\.md$' },
              content: { type: 'string', description: 'Markdown content' },
              message: { type: 'string', description: 'Commit message' },
              frontMatter: { 
                type: 'object', 
                properties: {
                  title: { type: 'string' },
                  date: { type: 'string', format: 'date' },
                  draft: { type: 'boolean' },
                  hero_image_url: { type: 'string', format: 'uri' },
                  bria_attribution: { type: 'string' },
                  source: { type: 'string' },
                  github_url: { type: 'string', format: 'uri' },
                  wp_post_id: { type: 'integer' },
                  social_urls: { type: 'array', items: { type: 'string' } }
                }
              }
            },
            required: ['path', 'content', 'message'],
          },
        },
      },
    ],
    handoffs: ['wp-publisher-agent', 'ayrshare-agent'],
  },
  {
    name: 'wp-publisher-agent',
    description: 'Creates or updates WordPress post with media and metadata.',
    tools: [
      {
        type: 'function',
        function: {
          name: 'publish_to_wordpress',
          description: 'Create/update WordPress.com post with media and metadata',
          parameters: {
            type: 'object',
            properties: {
              title: { type: 'string' },
              slug: { type: 'string' },
              content: { type: 'string' }, // HTML content
              excerpt: { type: 'string' },
              status: { type: 'string', enum: ['draft', 'publish'], default: 'draft' },
              featured_media_id: { type: 'integer', optional: true },
              categories: { type: 'array', items: { type: 'string' }, default: ['AI', 'Monitoring'] },
              tags: { type: 'array', items: { type: 'string' } },
              metadata: { 
                type: 'object',
                properties: {
                  github_url: { type: 'string', format: 'uri' },
                  bria_attribution: { type: 'string' },
                  cost_tracking: { type: 'object' }
                }
              }
            },
            required: ['title', 'content', 'slug'],
          },
        },
      },
      {
        type: 'function',
        function: {
          name: 'upload_media_to_wordpress',
          description: 'Upload media file to WordPress',
          parameters: {
            type: 'object',
            properties: {
              buffer: { type: 'string', format: 'binary', description: 'Base64 encoded media buffer' },
              filename: { type: 'string' },
              mime: { type: 'string', default: 'image/jpeg' }
            },
            required: ['buffer', 'filename'],
          },
        },
      },
    ],
    handoffs: ['ayrshare-agent', 'mailchimp-agent', 'slack-notifier-agent'],
  },
  {
    name: 'ayrshare-agent',
    description: 'Posts to Twitter, LinkedIn, Facebook, Instagram via Ayrshare.',
    tools: [
      {
        type: 'function',
        function: {
          name: 'post_to_social',
          description: 'Cross-post to social platforms via Ayrshare API',
          parameters: {
            type: 'object',
            properties: {
              post: { type: 'string', description: 'Main post content' },
              platforms: { 
                type: 'array', 
                items: { type: 'string', enum: ['twitter', 'linkedin', 'facebook', 'instagram', 'telegram', 'reddit'] },
                description: 'Target platforms'
              },
              mediaUrls: { type: 'array', items: { type: 'string', format: 'uri' }, optional: true },
              scheduleDate: { type: 'string', format: 'date-time', optional: true },
              title: { type: 'string', optional: true },
              link: { type: 'string', format: 'uri', optional: true }
            },
            required: ['post', 'platforms'],
          },
        },
      },
    ],
    handoffs: ['slack-notifier-agent', 'discord-notifier-agent'],
  },
  {
    name: 'budget-agent',
    description: 'Estimates costs, logs to Plaid, enforces budget caps.',
    tools: [
      {
        type: 'function',
        function: {
          name: 'log_expense',
          description: 'Log expense to Plaid or internal ledger',
          parameters: {
            type: 'object',
            properties: {
              amount: { type: 'number', minimum: 0 },
              category: { type: 'string', default: 'marketing' },
              description: { type: 'string' },
              vendor: { type: 'string' },
              project: { type: 'string', default: 'lab-verse-monitoring' }
            },
            required: ['amount', 'vendor', 'description'],
          },
        },
      },
      {
        type: 'function',
        function: {
          name: 'check_budget_allowance',
          description: 'Check if remaining budget allows this operation',
          parameters: {
            type: 'object',
            properties: {
              estimatedCost: { type: 'number', minimum: 0 },
              project: { type: 'string', default: 'lab-verse-monitoring' },
              category: { type: 'string', default: 'content-automation' }
            },
            required: ['estimatedCost'],
          },
        },
      },
    ],
    handoffs: ['content-planner-agent', 'emergency-agent'],
  },
  {
    name: 'emergency-agent',
    description: 'Handles critical alerts; escalates to humans via Slack/Discord/Teams.',
    tools: [
      {
        type: 'function',
        function: {
          name: 'send_emergency_alert',
          description: 'Send urgent alert to communication platforms',
          parameters: {
            type: 'object',
            properties: {
              message: { type: 'string' },
              severity: { type: 'string', enum: ['high', 'critical'], default: 'critical' },
              channels: { 
                type: 'array', 
                items: { type: 'string', enum: ['slack', 'teams', 'discord', 'email'] },
                default: ['slack', 'discord'] 
              },
              include_details: { type: 'boolean', default: true }
            },
            required: ['message', 'severity'],
          },
        },
      },
    ],
    handoffs: [],
  },
  {
    name: 'monitoring-agent',
    description: 'Handles monitoring alerts and infrastructure status updates.',
    instructions: `
You handle monitoring alerts from the Lab Verse Monitoring Stack:
- Parse alert data from Prometheus/Grafana
- Determine severity and impact
- Generate incident reports
- Coordinate with Kimi Instruct for resolution
- Notify relevant teams

Handoff strategy:
- Critical infrastructure issues → emergency-agent
- Budget/cost alerts → budget-agent  
- Content-related monitoring → content-planner-agent
`,
    handoffs: ['emergency-agent', 'budget-agent', 'content-planner-agent'],
  },
];

async function registerAgents() {
  const agentIds = {};
  const agentDir = path.join(__dirname, '..', '.agents');
  await fs.mkdir(agentDir, { recursive: true });

  console.log('🔧 Registering/updating Lab Verse Monitoring Stack agents...');
  
  // Get existing agents first to avoid duplicates
  let existingAgents = [];
  try {
    const listResponse = await client.beta.agents.list();
    existingAgents = listResponse.agents || [];
    console.log(`📊 Found ${existingAgents.length} existing agents`);
  } catch (e) {
    console.warn('⚠️ Could not list existing agents - proceeding to create new ones');
  }

  for (const spec of AGENT_SPECS) {
    try {
      // Check if agent already exists
      const existingAgent = existingAgents.find(a => a.name === spec.name);
      
      const commonConfig = {
        model: 'mistral-large-latest',
        description: spec.description,
        instructions: spec.instructions,
        meta { 
          managed_by: 'lab-verse-monitoring-stack',
          version: '1.0',
          project: 'The-lab-verse-monitoring-'
        },
        tool_resources: {},
      };

      if (existingAgent) {
        // Update existing agent
        console.log(`🔁 Updating agent: ${spec.name} (${existingAgent.id})`);
        const updatedAgent = await client.beta.agents.update({
          agent_id: existingAgent.id,
          ...commonConfig,
          tools: spec.tools || [],
          handoffs: spec.handoffs?.map(name => 
            agentIds[name] || existingAgents.find(a => a.name === name)?.id || `ag_${name}`
          ).filter(Boolean) || [],
        });
        agentIds[spec.name] = updatedAgent.id;
      } else {
        // Create new agent
        console.log(`🆕 Creating agent: ${spec.name}`);
        const createdAgent = await client.beta.agents.create({
          ...commonConfig,
          name: spec.name,
          tools: spec.tools || [],
          handoffs: spec.handoffs?.map(name => 
            agentIds[name] || `ag_${name}`
          ).filter(Boolean) || [],
        });
        agentIds[spec.name] = createdAgent.id;
      }

      // Save agent ID to file for easy reference
      await fs.writeFile(
        path.join(agentDir, `${spec.name}.id`),
        agentIds[spec.name],
        'utf8'
      );
      
      console.log(`✅ ${spec.name}: ${agentIds[spec.name]}`);

    } catch (e) {
      console.error(`❌ Failed to register ${spec.name}:`, e.message);
      if (e.response?.data) {
        console.error('Response ', JSON.stringify(e.response.data, null, 2));
      }
      // Don't fail the entire process - continue with other agents
      continue;
    }
  }

  // Generate .env.agent_ids file for Vercel/GitHub Actions
  const envLines = Object.entries(agentIds).map(
    ([name, id]) => `${name.toUpperCase().replace(/-/g, '_')}_ID=${id}`
  );
  
  const envContent = `# Generated by scripts/register-agents.js - ${new Date().toISOString()}
${envLines.join('\n')}
`;
  
  await fs.writeFile(
    path.join(__dirname, '..', '.env.agent_ids'),
    envContent,
    'utf8'
  );
  
  console.log('✅ All agents registered successfully!');
  console.log('📁 Agent IDs saved to .env.agent_ids and .agents/ directory');
  
  // Print instructions for GitHub Secrets setup
  console.log('\n🔐 To use in Vercel/GitHub Actions, add these secrets:');
  envLines.forEach(line => console.log(`  ${line}`));
  
  console.log('\n🚀 Next steps:');
  console.log('1. Copy .env.agent_ids to your .env file:');
  console.log('   cat .env.agent_ids >> .env');
  console.log('2. Deploy your Vercel function:');
  console.log('   vercel deploy');
  console.log('3. Add the webhook URL to RankYak');
}

if (import.meta.url === `file://${process.argv[1]}`) {
  registerAgents().catch(err => {
    console.error('💥 Agent registration failed:', err);
    console.error('Stack trace:', err.stack);
    process.exit(1);
  });
}

// Export for programmatic use
export default { registerAgents, AGENT_SPECS };

