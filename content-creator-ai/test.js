/**
 * Simple test script to verify the application works
 * Run: node test.js
 */

const axios = require('axios');

const BASE_URL = process.env.BASE_URL || 'http://localhost:3000';
const API_KEY = process.env.API_KEY || 'your-webhook-api-key-here';

console.log('🧪 Content Creator AI - Test Suite\n');
console.log(`Testing server at: ${BASE_URL}\n`);

async function testHealthCheck() {
  try {
    console.log('1️⃣  Testing health check...');
    const response = await axios.get(`${BASE_URL}/api/health`);
    console.log('   ✅ Health check passed');
    console.log('   Status:', response.data.status);
    console.log('   Enabled providers:', Object.entries(response.data.providers)
      .filter(([_, enabled]) => enabled)
      .map(([name]) => name)
      .join(', '));
    console.log('');
    return true;
  } catch (error) {
    console.log('   ❌ Health check failed:', error.message);
    console.log('');
    return false;
  }
}

async function testTestEndpoint() {
  try {
    console.log('2️⃣  Testing test endpoint (no real APIs)...');
    const response = await axios.get(`${BASE_URL}/api/test`);
    console.log('   ✅ Test endpoint passed');
    console.log('   Request ID:', response.data.requestId);
    console.log('   Content type:', response.data.content.type);
    console.log('');
    return true;
  } catch (error) {
    console.log('   ❌ Test endpoint failed:', error.message);
    console.log('');
    return false;
  }
}

async function testAuthenticationRequired() {
  try {
    console.log('3️⃣  Testing authentication (should fail without API key)...');
    await axios.post(`${BASE_URL}/api/content`, {
      topic: 'test',
      media_type: 'text'
    });
    console.log('   ❌ Authentication not enforced!');
    console.log('');
    return false;
  } catch (error) {
    if (error.response && error.response.status === 401) {
      console.log('   ✅ Authentication properly enforced');
      console.log('');
      return true;
    }
    console.log('   ❌ Unexpected error:', error.message);
    console.log('');
    return false;
  }
}

async function testContentGeneration() {
  try {
    console.log('4️⃣  Testing content generation with API key...');
    const response = await axios.post(`${BASE_URL}/api/content`, {
      topic: 'Test topic for automated testing',
      media_type: 'text',
      length: 'short',
      provider: 'auto',
      enable_research: false,
      include_seo: false,
      include_social: false
    }, {
      headers: {
        'X-API-Key': API_KEY,
        'Content-Type': 'application/json'
      },
      timeout: 60000 // 60 second timeout
    });

    if (response.data.success) {
      console.log('   ✅ Content generation successful');
      console.log('   Request ID:', response.data.requestId);
      console.log('   Provider used:', response.data.metadata.provider);
      console.log('   Content length:', response.data.content.content.length, 'chars');
      console.log('   Total cost: $' + response.data.costs.totalCost.toFixed(4));
      console.log('');
      return true;
    } else {
      console.log('   ❌ Content generation failed:', response.data.message);
      console.log('');
      return false;
    }
  } catch (error) {
    if (error.response) {
      console.log('   ❌ Content generation failed:', error.response.data.message || error.message);
    } else {
      console.log('   ❌ Content generation failed:', error.message);
    }
    console.log('   ℹ️  This is expected if no AI providers are configured');
    console.log('');
    return false;
  }
}

async function testStats() {
  try {
    console.log('5️⃣  Testing stats endpoint...');
    const response = await axios.get(`${BASE_URL}/api/stats`, {
      headers: {
        'X-API-Key': API_KEY
      }
    });
    console.log('   ✅ Stats endpoint passed');
    console.log('   Total requests:', response.data.stats.totalRequests);
    console.log('   Total cost: $' + response.data.stats.totalCost.toFixed(4));
    console.log('');
    return true;
  } catch (error) {
    console.log('   ❌ Stats endpoint failed:', error.message);
    console.log('');
    return false;
  }
}

async function runAllTests() {
  console.log('═══════════════════════════════════════════════════════\n');
  
  const results = [];
  
  results.push(await testHealthCheck());
  results.push(await testTestEndpoint());
  results.push(await testAuthenticationRequired());
  
  // Only run real API tests if explicitly requested
  if (process.env.RUN_FULL_TESTS === 'true') {
    results.push(await testContentGeneration());
    results.push(await testStats());
  } else {
    console.log('ℹ️  Skipping real API tests (set RUN_FULL_TESTS=true to enable)\n');
  }
  
  console.log('═══════════════════════════════════════════════════════');
  console.log('\n📊 Test Results:');
  console.log(`   Passed: ${results.filter(r => r).length}/${results.length}`);
  console.log(`   Failed: ${results.filter(r => !r).length}/${results.length}`);
  
  const allPassed = results.every(r => r);
  
  if (allPassed) {
    console.log('\n✅ All tests passed!\n');
    process.exit(0);
  } else {
    console.log('\n❌ Some tests failed\n');
    process.exit(1);
  }
}

// Handle errors
process.on('unhandledRejection', (error) => {
  console.error('❌ Unhandled error:', error.message);
  process.exit(1);
});

// Run tests
console.log('Starting tests in 2 seconds...\n');
setTimeout(runAllTests, 2000);
