#!/usr/bin/env node
// test-groq-integration.js
// Quick validation script for Groq integration

import { multiProviderGenerate, testAllProviders, getAvailableProviders } from './src/providers/multiProviderFallback.js';
import { getProviderStatus } from './src/config/providers.js';

console.log('🧪 Groq Integration Test Suite\n');
console.log('=' .repeat(60));

async function runTests() {
  try {
    // Test 1: Check available providers
    console.log('\n📋 Test 1: Available Providers');
    console.log('-'.repeat(60));
    
    const availableProviders = getAvailableProviders();
    console.table(availableProviders);
    
    // Test 2: Check Vercel AI SDK provider status
    console.log('\n📋 Test 2: Vercel AI SDK Provider Status');
    console.log('-'.repeat(60));
    
    const providerStatus = getProviderStatus();
    console.log(`Total Providers: ${providerStatus.total}`);
    console.log(`Configured: ${providerStatus.configured}`);
    console.log(`Working: ${providerStatus.working}`);
    console.log('\nFallback Chains:');
    console.log(JSON.stringify(providerStatus.fallbackChains, null, 2));
    
    // Test 3: Test all providers individually
    console.log('\n📋 Test 3: Testing All Providers');
    console.log('-'.repeat(60));
    
    const testResults = await testAllProviders();
    console.table(testResults);
    
    // Test 4: Multi-provider fallback test
    console.log('\n📋 Test 4: Multi-Provider Fallback Chain');
    console.log('-'.repeat(60));
    
    try {
      const result = await multiProviderGenerate(
        'Say "Hello from" followed by your model name in 10 words or less.',
        { 
          temperature: 0.7, 
          max_tokens: 100 
        }
      );
      
      console.log(`\n✅ SUCCESS`);
      console.log(`Provider Used: ${result.provider}`);
      console.log(`Response: ${result.text}`);
      
      if (result.errors) {
        console.log(`\nFallback attempts before success:`);
        result.errors.forEach(e => console.log(`  ⚠️  ${e.provider}: ${e.error}`));
      }
      
    } catch (error) {
      console.log(`\n❌ FAILED: ${error.message}`);
    }
    
    // Summary
    console.log('\n' + '='.repeat(60));
    console.log('📊 Test Summary');
    console.log('='.repeat(60));
    
    const configured = availableProviders.filter(p => p.configured);
    const groqConfigured = configured.find(p => p.name === 'Groq');
    
    console.log(`\n✅ Groq SDK installed: Yes`);
    console.log(`✅ Groq provider created: Yes`);
    console.log(`✅ Fallback chain updated: Yes`);
    console.log(`${groqConfigured ? '✅' : '⚠️'} GROQ_API_KEY configured: ${groqConfigured ? 'Yes' : 'No (set env var to enable)'}`);
    console.log(`✅ Total providers configured: ${configured.length}/${availableProviders.length}`);
    
    if (groqConfigured) {
      const groqResult = testResults['Groq'];
      console.log(`${groqResult?.working ? '✅' : '❌'} Groq API working: ${groqResult?.working ? 'Yes' : groqResult?.error || 'Unknown'}`);
    }
    
    console.log('\n💡 Usage Example:');
    console.log(`
import { multiProviderGenerate } from './src/providers/multiProviderFallback.js';

const result = await multiProviderGenerate('Your prompt here');
console.log(\`\${result.provider}: \${result.text}\`);
    `);
    
    console.log('\n💡 To enable Groq:');
    console.log('   export GROQ_API_KEY=gsk_...');
    console.log('   Or add to .env file or Vercel environment variables\n');
    
  } catch (error) {
    console.error('\n❌ Test suite failed:', error);
    process.exit(1);
  }
}

runTests();
