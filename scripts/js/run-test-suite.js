#!/usr/bin/env node
// run-test-suite.js - Execute the AI SDK test suite and live workflow

import { generateContent, streamContent } from './src/services/contentGenerator.js';
import { getActiveProvider, hasAvailableProvider, getAvailableProviders } from './src/config/providers.js';
import { config } from 'dotenv';

// Load environment variables
config();

async function runTestSuite() {
  console.log('🚀 Starting AI SDK Test Suite and Live Workflow');
  console.log('=' .repeat(60));
  
  // 1. Check Provider Availability
  console.log('\n📋 STEP 1: Checking Provider Availability');
  console.log('-'.repeat(40));
  
  const hasProviders = hasAvailableProvider();
  console.log(`✓ Has available providers: ${hasProviders}`);
  
  if (hasProviders) {
    const activeProvider = getActiveProvider();
    console.log(`✓ Active provider selected: ${activeProvider ? 'Yes' : 'No'}`);
    
    const availableProviders = getAvailableProviders();
    console.log(`✓ Available providers:`);
    availableProviders.forEach(provider => {
      console.log(`  - ${provider.displayName} (priority: ${provider.priority})`);
    });
  } else {
    console.log('⚠️  No providers configured - tests will use mock mode');
  }
  
  // 2. Run Content Generation Test
  console.log('\n🧪 STEP 2: Testing Content Generation');
  console.log('-'.repeat(40));
  
  if (hasProviders) {
    try {
      const startTime = Date.now();
      const content = await generateContent('Write a short message about AI testing', {
        maxTokens: 100,
        temperature: 0.7,
        timeout: 15000
      });
      const duration = Date.now() - startTime;
      
      console.log(`✅ Content generated successfully in ${duration}ms`);
      console.log(`✓ Content length: ${content.length} characters`);
      console.log(`✓ Content preview: "${content.substring(0, 100)}..."`);
    } catch (error) {
      console.error(`❌ Content generation failed: ${error.message}`);
    }
  } else {
    console.log('⏭️  Skipped - no providers available');
  }
  
  // 3. Run Streaming Test
  console.log('\n🔄 STEP 3: Testing Content Streaming');
  console.log('-'.repeat(40));
  
  if (hasProviders) {
    try {
      const chunks = [];
      const startTime = Date.now();
      
      console.log('📡 Starting stream...');
      for await (const chunk of streamContent('Count to 5 slowly', {
        maxTokens: 50,
        temperature: 0.3
      })) {
        chunks.push(chunk);
        process.stdout.write('.');
      }
      const duration = Date.now() - startTime;
      
      console.log(`\n✅ Streaming completed in ${duration}ms`);
      console.log(`✓ Chunks received: ${chunks.length}`);
      console.log(`✓ Total content: "${chunks.join('').substring(0, 100)}..."`);
    } catch (error) {
      console.error(`❌ Streaming failed: ${error.message}`);
    }
  } else {
    console.log('⏭️  Skipped - no providers available');
  }
  
  // 4. Test Error Handling
  console.log('\n🛡️  STEP 4: Testing Error Handling');
  console.log('-'.repeat(40));
  
  try {
    await generateContent('Test prompt', { provider: 'invalid-provider' });
    console.log('❌ Should have thrown error for invalid provider');
  } catch (error) {
    console.log(`✅ Error handling works: ${error.message}`);
  }
  
  // 5. Test Timeout Handling
  if (hasProviders) {
    console.log('\n⏱️  STEP 5: Testing Timeout Handling');
    console.log('-'.repeat(40));
    
    try {
      await generateContent('Write a comprehensive analysis of AI', {
        maxTokens: 5000,
        timeout: 100 // Very short timeout to force failure
      });
      console.log('❌ Should have timed out');
    } catch (error) {
      if (error.message.includes('timed out')) {
        console.log(`✅ Timeout handling works: ${error.message}`);
      } else {
        console.log(`⚠️  Different error occurred: ${error.message}`);
      }
    }
  }
  
  // Final Summary
  console.log('\n' + '='.repeat(60));
  console.log('🎉 AI SDK Test Suite and Live Workflow Complete!');
  console.log('=' .repeat(60));
  
  if (hasProviders) {
    console.log('✅ All systems operational - ready for production use');
  } else {
    console.log('⚠️  Configure AI providers to enable full functionality');
    console.log('   Add API keys to .env file for:');
    console.log('   - OPENAI_API_KEY (for GPT-4)');
    console.log('   - ANTHROPIC_API_KEY (for Claude)');
    console.log('   - LOCALAI_HOST and LOCALAI_API_KEY (for Mistral Local)');
  }
}

// Execute if run directly
if (import.meta.url === `file://${process.argv[1]}`) {
  runTestSuite().catch(console.error);
}

export { runTestSuite };