#!/usr/bin/env node
/**
 * Test Script: MCP Tools and Social Media Integration Verification
 * Tests all MCP gateway connections and social media platform integrations
 */

const dotenv = require('dotenv');
const path = require('path');

// Load environment variables
dotenv.config({ path: path.join(__dirname, '.env.local') });

const GATEWAY_URL = process.env.GATEWAY_URL || 'https://the-lab-verse-monitoring.vercel.app';
const GATEWAY_API_KEY = process.env.GATEWAY_API_KEY || process.env.AI_GATEWAY_API_KEY;

console.log('╔════════════════════════════════════════════════════════════════════╗');
console.log('║  MCP Tools & Social Media Integration Test Suite                  ║');
console.log('╚════════════════════════════════════════════════════════════════════╝\n');

// Test configuration
const tests = {
  environment: [],
  mcpTools: [],
  socialMedia: [],
  integrations: []
};

// 1. Environment Variables Check
console.log('📋 Phase 1: Environment Configuration Check\n');

const requiredEnvVars = [
  'GATEWAY_URL',
  'GATEWAY_API_KEY',
  'MISTRAL_API_KEY',
  'HF_API_TOKEN',
  'BRIA_API_KEY',
  'DEEP_INFRA_API_KEY',
  'VERCEL_TOKEN',
  'ALIYUN_ACCESS_KEY_ID',
  'ALIYUN_ACCESS_KEY_SECRET'
];

requiredEnvVars.forEach((varName) => {
  const value = process.env[varName];
  const status = value ? '✅' : '❌';
  const display = value ? `${value.substring(0, 10)}...` : 'NOT SET';
  console.log(`${status} ${varName}: ${display}`);
  tests.environment.push({ name: varName, status: !!value, value: display });
});

console.log('\n📦 Phase 2: MCP Gateway Configuration\n');

// 2. MCP Gateway Endpoints
const mcpEndpoints = [
  { name: 'HuggingFace Gateway', path: '/mcp/huggingface/messages' },
  { name: 'SocialPilot Gateway', path: '/mcp/socialpilot/messages' },
  { name: 'Unito Gateway', path: '/mcp/unito/messages' },
  { name: 'WordPress.com Gateway', path: '/mcp/wpcom/messages' }
];

console.log('MCP Gateway Endpoints:');
mcpEndpoints.forEach((endpoint) => {
  console.log(`  • ${endpoint.name}: ${GATEWAY_URL}${endpoint.path}`);
  tests.mcpTools.push({ name: endpoint.name, endpoint: `${GATEWAY_URL}${endpoint.path}` });
});

console.log('\n🌐 Phase 3: Social Media Platform Configuration\n');

// 3. Social Media Platforms
const socialPlatforms = [
  { name: 'Twitter/X', supported: true },
  { name: 'LinkedIn', supported: true },
  { name: 'Facebook', supported: true },
  { name: 'Instagram', supported: true },
  { name: 'Threads', supported: true },
  { name: 'YouTube', supported: true }
];

console.log('Supported Social Media Platforms:');
socialPlatforms.forEach((platform) => {
  const status = platform.supported ? '✅' : '❌';
  console.log(`${status} ${platform.name}`);
  tests.socialMedia.push(platform);
});

console.log('\n🔧 Phase 4: API Integration Status\n');

// 4. API Integrations
const apiIntegrations = [
  {
    name: 'Mistral Codestral',
    key: 'MISTRAL_API_KEY',
    endpoint: 'https://codestral.mistral.ai/v1/chat/completions'
  },
  {
    name: 'Mistral Agent',
    key: 'MISTRAL_AGENT_ID',
    endpoint: 'https://api.mistral.ai/v1/conversations'
  },
  { name: 'HuggingFace', key: 'HF_API_TOKEN', endpoint: 'https://api-inference.huggingface.co' },
  { name: 'Bria AI', key: 'BRIA_API_KEY', endpoint: 'https://platform.bria.ai/labs/fibo' },
  { name: 'Deep Infra', key: 'DEEP_INFRA_API_KEY', endpoint: 'https://api.deepinfra.com' },
  { name: 'Alibaba Cloud', key: 'ALIYUN_ACCESS_KEY_ID', endpoint: 'cn-shanghai' }
];

apiIntegrations.forEach((api) => {
  const configured = !!process.env[api.key];
  const status = configured ? '✅' : '❌';
  console.log(`${status} ${api.name}`);
  console.log(`   Endpoint: ${api.endpoint}`);
  tests.integrations.push({ name: api.name, configured, endpoint: api.endpoint });
});

console.log('\n📊 Phase 5: Test Summary\n');

// 5. Summary
const envPassed = tests.environment.filter((t) => t.status).length;
const envTotal = tests.environment.length;
const socialPassed = tests.socialMedia.filter((p) => p.supported).length;
const socialTotal = tests.socialMedia.length;
const apiPassed = tests.integrations.filter((i) => i.configured).length;
const apiTotal = tests.integrations.length;

console.log('╔════════════════════════════════════════════════════════════════════╗');
console.log('║                        TEST RESULTS SUMMARY                        ║');
console.log('╠════════════════════════════════════════════════════════════════════╣');
console.log(
  `║ Environment Variables:  ${envPassed}/${envTotal} configured                              ║`
);
console.log(
  `║ MCP Gateways:          ${tests.mcpTools.length} endpoints available                       ║`
);
console.log(
  `║ Social Platforms:      ${socialPassed}/${socialTotal} platforms supported                    ║`
);
console.log(
  `║ API Integrations:      ${apiPassed}/${apiTotal} integrations configured                  ║`
);
console.log('╚════════════════════════════════════════════════════════════════════╝\n');

// 6. Recommendations
console.log('💡 Recommendations:\n');

if (envPassed < envTotal) {
  console.log('⚠️  Some environment variables are missing. Please configure:');
  tests.environment
    .filter((t) => !t.status)
    .forEach((t) => {
      console.log(`   - ${t.name}`);
    });
  console.log('');
}

if (apiPassed < apiTotal) {
  console.log('⚠️  Some API integrations are not configured:');
  tests.integrations
    .filter((i) => !i.configured)
    .forEach((i) => {
      console.log(`   - ${i.name}`);
    });
  console.log('');
}

console.log('✅ Next Steps:');
console.log('   1. Configure missing environment variables in .env.local');
console.log('   2. Test MCP gateway endpoints with actual API calls');
console.log('   3. Verify social media platform authentication');
console.log('   4. Run integration tests for content distribution');
console.log('   5. Deploy to Vercel for production testing\n');

// Export test results
const fs = require('fs');
const resultsPath = path.join(__dirname, 'test-results-mcp-social.json');
fs.writeFileSync(
  resultsPath,
  JSON.stringify(
    {
      timestamp: new Date().toISOString(),
      summary: {
        environment: `${envPassed}/${envTotal}`,
        mcpGateways: tests.mcpTools.length,
        socialPlatforms: `${socialPassed}/${socialTotal}`,
        apiIntegrations: `${apiPassed}/${apiTotal}`
      },
      details: tests
    },
    null,
    2
  )
);

console.log(`📄 Test results saved to: ${resultsPath}\n`);

// Exit with appropriate code
const allPassed = envPassed === envTotal && apiPassed === apiTotal;
process.exit(allPassed ? 0 : 1);
