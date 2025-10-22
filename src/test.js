#!/usr/bin/env node

import { ProviderFactory } from './services/ProviderFactory.js';
import { ContentGenerator } from './services/ContentGenerator.js';
import { getAvailableProviders } from './config/providers.js';
import { logger } from './utils/logger.js';

async function runTests() {
  console.log('🧪 Running AI Content Creation Suite Tests...\n');

  try {
    // Test 1: Provider Availability
    console.log('1. Testing provider availability...');
    const providers = getAvailableProviders();
    console.log(`   Available providers: ${providers.map(p => p.name).join(', ')}`);
    
    if (providers.length === 0) {
      console.log('   ⚠️  No providers configured. Please set up API keys in .env file.');
    }

    // Test 2: Provider Connections
    console.log('\n2. Testing provider connections...');
    const testResults = await ProviderFactory.testAllProviders();
    
    Object.entries(testResults).forEach(([provider, result]) => {
      if (result.success) {
        console.log(`   ✅ ${provider}: Connected successfully`);
      } else {
        console.log(`   ❌ ${provider}: ${result.error}`);
      }
    });

    // Test 3: Content Generation (if providers available)
    const workingProviders = Object.entries(testResults)
      .filter(([_, result]) => result.success)
      .map(([provider, _]) => provider);

    if (workingProviders.length > 0) {
      console.log('\n3. Testing content generation...');
      const contentGenerator = new ContentGenerator();
      
      const testRequest = {
        topic: 'Test Content Generation',
        audience: 'developers',
        tone: 'professional',
        language: 'en',
        mediaType: 'text',
        provider: workingProviders[0],
        keywords: ['test', 'ai', 'content'],
        length: 'short'
      };

      try {
        const result = await contentGenerator.generateContent(testRequest);
        console.log(`   ✅ Content generated successfully with ${result.metadata.provider}`);
        console.log(`   📝 Content preview: ${result.content.content.substring(0, 100)}...`);
        console.log(`   💰 Cost: $${result.metadata.cost.toFixed(4)}`);
      } catch (error) {
        console.log(`   ❌ Content generation failed: ${error.message}`);
      }
    } else {
      console.log('\n3. Skipping content generation test (no working providers)');
    }

    // Test 4: System Health
    console.log('\n4. Testing system health...');
    try {
      const response = await fetch(`http://localhost:${process.env.PORT || 3000}/health`);
      const health = await response.json();
      
      if (health.status === 'healthy') {
        console.log('   ✅ System health check passed');
      } else {
        console.log(`   ⚠️  System health: ${health.status}`);
      }
    } catch (error) {
      console.log('   ❌ System health check failed (server not running?)');
    }

    console.log('\n🎉 Tests completed!');
    
    // Summary
    const workingCount = workingProviders.length;
    const totalCount = Object.keys(testResults).length;
    
    console.log(`\n📊 Summary:`);
    console.log(`   Working providers: ${workingCount}/${totalCount}`);
    console.log(`   System status: ${workingCount > 0 ? 'Ready' : 'Needs configuration'}`);
    
    if (workingCount === 0) {
      console.log('\n💡 Next steps:');
      console.log('   1. Configure at least one API key in .env file');
      console.log('   2. Start the server: npm start');
      console.log('   3. Open http://localhost:3000 in your browser');
    }

  } catch (error) {
    console.error('❌ Test suite failed:', error);
    process.exit(1);
  }
}

// Run tests if this file is executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
  runTests().catch(console.error);
}

export { runTests };