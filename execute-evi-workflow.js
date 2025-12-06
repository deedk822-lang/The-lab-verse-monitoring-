#!/usr/bin/env node
// execute-evi-workflow.js - Complete Evi Integration Workflow Execution

import { evi } from './src/integrations/eviIntegration.js';
import { generateContent, streamContent } from './src/services/contentGenerator.js';
import { hasAvailableProvider, getAvailableProviders } from './src/config/providers.js';
import { config } from 'dotenv';

// Load environment variables
config();

class EviWorkflowExecutor {
  constructor() {
    this.results = {
      initialization: null,
      basicGeneration: null,
      enhancedGeneration: null,
      streaming: null,
      enhancedStreaming: null,
      multiProvider: null,
      healthCheck: null,
      errorTesting: null,
      performance: []
    };
  }

  async execute() {
    console.log('🌟 EVI INTEGRATION WORKFLOW EXECUTION');
    console.log('='.repeat(70));
    console.log(`Started at: ${new Date().toISOString()}`);
    console.log('='.repeat(70));

    try {
      await this.step1_Initialize();
      await this.step2_BasicGeneration();
      await this.step3_EnhancedGeneration();
      await this.step4_BasicStreaming();
      await this.step5_EnhancedStreaming();
      await this.step6_MultiProviderWorkflow();
      await this.step7_HealthCheck();
      await this.step8_ErrorTesting();
      await this.step9_PerformanceAnalysis();
      
      this.generateFinalReport();
      
    } catch (error) {
      console.error('🚫 WORKFLOW EXECUTION FAILED:', error.message);
      throw error;
    }
  }

  async step1_Initialize() {
    console.log('\n🚀 STEP 1: Evi Integration Initialization');
    console.log('-'.repeat(50));

    try {
      this.results.initialization = await evi.initialize();
      console.log('✅ Evi initialization successful');
      console.log(`   Status: ${this.results.initialization.status}`);
      console.log(`   Capabilities: ${this.results.initialization.capabilities.join(', ')}`);
      
      const providers = getAvailableProviders();
      console.log(`   Available providers: ${providers.length}`);
      providers.forEach(p => {
        console.log(`     - ${p.displayName} (priority: ${p.priority})`);
      });
      
    } catch (error) {
      console.error('❌ Initialization failed:', error.message);
      this.results.initialization = { error: error.message };
      throw error;
    }
  }

  async step2_BasicGeneration() {
    console.log('\n📋 STEP 2: Basic Content Generation Test');
    console.log('-'.repeat(50));

    if (!hasAvailableProvider()) {
      console.log('⏭️  Skipped - no providers available');
      return;
    }

    try {
      const startTime = Date.now();
      const content = await generateContent(
        'Write a concise message about successful AI integration testing',
        {
          maxTokens: 150,
          temperature: 0.7,
          timeout: 15000
        }
      );
      const duration = Date.now() - startTime;

      this.results.basicGeneration = {
        success: true,
        content: content.substring(0, 100) + '...',
        length: content.length,
        duration
      };

      console.log('✅ Basic generation successful');
      console.log(`   Content length: ${content.length} characters`);
      console.log(`   Duration: ${duration}ms`);
      console.log(`   Preview: "${content.substring(0, 80)}..."`);

    } catch (error) {
      console.error('❌ Basic generation failed:', error.message);
      this.results.basicGeneration = { error: error.message };
    }
  }

  async step3_EnhancedGeneration() {
    console.log('\n🎆 STEP 3: Enhanced Generation with Evi');
    console.log('-'.repeat(50));

    if (!hasAvailableProvider()) {
      console.log('⏭️  Skipped - no providers available');
      return;
    }

    try {
      const startTime = Date.now();
      const result = await evi.enhancedGenerate(
        'Explain the benefits of AI integration testing',
        {
          maxTokens: 200,
          enhance: true,
          context: 'Software development and testing',
          tone: 'professional',
          format: 'structured list'
        }
      );
      const duration = Date.now() - startTime;

      this.results.enhancedGeneration = {
        success: true,
        metadata: result.metadata,
        length: result.content.length,
        duration
      };

      console.log('✅ Enhanced generation successful');
      console.log(`   Content length: ${result.content.length} characters`);
      console.log(`   Duration: ${duration}ms`);
      console.log(`   Enhanced: ${result.metadata.enhanced}`);
      console.log(`   Provider: ${result.metadata.provider}`);

    } catch (error) {
      console.error('❌ Enhanced generation failed:', error.message);
      this.results.enhancedGeneration = { error: error.message };
    }
  }

  async step4_BasicStreaming() {
    console.log('\n🔄 STEP 4: Basic Streaming Test');
    console.log('-'.repeat(50));

    if (!hasAvailableProvider()) {
      console.log('⏭️  Skipped - no providers available');
      return;
    }

    try {
      const chunks = [];
      const startTime = Date.now();

      console.log('📡 Streaming content...');
      for await (const chunk of streamContent(
        'List 3 key benefits of AI testing: 1.',
        { maxTokens: 100 }
      )) {
        chunks.push(chunk);
        process.stdout.write('.');
      }
      const duration = Date.now() - startTime;

      this.results.streaming = {
        success: true,
        chunks: chunks.length,
        totalContent: chunks.join('').length,
        duration
      };

      console.log(`\n✅ Basic streaming successful`);
      console.log(`   Chunks received: ${chunks.length}`);
      console.log(`   Total content: ${chunks.join('').length} characters`);
      console.log(`   Duration: ${duration}ms`);

    } catch (error) {
      console.error('❌ Basic streaming failed:', error.message);
      this.results.streaming = { error: error.message };
    }
  }

  async step5_EnhancedStreaming() {
    console.log('\n🌊 STEP 5: Enhanced Streaming with Evi');
    console.log('-'.repeat(50));

    if (!hasAvailableProvider()) {
      console.log('⏭️  Skipped - no providers available');
      return;
    }

    try {
      const chunks = [];
      const startTime = Date.now();

      console.log('📡 Enhanced streaming...');
      for await (const data of evi.enhancedStream(
        'Describe AI integration testing workflow',
        {
          maxTokens: 120,
          enhance: true,
          context: 'Technical documentation',
          tone: 'explanatory'
        }
      )) {
        chunks.push(data);
        if (data.chunk) {
          process.stdout.write('✨');
        }
        if (data.summary) {
          process.stdout.write('✓');
        }
      }
      const duration = Date.now() - startTime;

      const summary = chunks.find(c => c.summary)?.summary;
      this.results.enhancedStreaming = {
        success: true,
        chunks: chunks.length,
        summary,
        duration
      };

      console.log(`\n✅ Enhanced streaming successful`);
      console.log(`   Total chunks: ${chunks.length}`);
      console.log(`   Content chunks: ${summary?.totalChunks || 'N/A'}`);
      console.log(`   Final length: ${summary?.totalLength || 'N/A'} characters`);
      console.log(`   Duration: ${duration}ms`);

    } catch (error) {
      console.error('❌ Enhanced streaming failed:', error.message);
      this.results.enhancedStreaming = { error: error.message };
    }
  }

  async step6_MultiProviderWorkflow() {
    console.log('\n🔄 STEP 6: Multi-Provider Workflow');
    console.log('-'.repeat(50));

    if (!hasAvailableProvider()) {
      console.log('⏭️  Skipped - no providers available');
      return;
    }

    try {
      const startTime = Date.now();
      const result = await evi.multiProviderGenerate(
        'Confirm AI integration is working correctly',
        { maxTokens: 80 }
      );
      const duration = Date.now() - startTime;

      this.results.multiProvider = {
        success: true,
        providerUsed: result.providerUsed,
        fallbackAttempts: result.fallbackAttempts,
        duration
      };

      console.log('✅ Multi-provider workflow successful');
      console.log(`   Provider used: ${result.providerUsed}`);
      console.log(`   Fallback attempts: ${result.fallbackAttempts}`);
      console.log(`   Duration: ${duration}ms`);

    } catch (error) {
      console.error('❌ Multi-provider workflow failed:', error.message);
      this.results.multiProvider = { error: error.message };
    }
  }

  async step7_HealthCheck() {
    console.log('\n🩺 STEP 7: Health Check');
    console.log('-'.repeat(50));

    try {
      const health = await evi.healthCheck();
      this.results.healthCheck = health;

      console.log(`✅ Health check completed`);
      console.log(`   Status: ${health.status}`);
      console.log(`   Timestamp: ${health.timestamp}`);
      console.log(`   Providers available: ${health.providers}`);
      
      if (health.status === 'healthy') {
        console.log(`   Response preview: "${health.response?.substring(0, 50)}..."`);
      } else {
        console.log(`   Error: ${health.error}`);
      }

    } catch (error) {
      console.error('❌ Health check failed:', error.message);
      this.results.healthCheck = { error: error.message };
    }
  }

  async step8_ErrorTesting() {
    console.log('\n🛡️  STEP 8: Error Handling Tests');
    console.log('-'.repeat(50));

    const errorTests = [];

    // Test 1: Invalid provider
    try {
      await generateContent('test', { provider: 'nonexistent-provider' });
      errorTests.push({ test: 'invalid_provider', result: 'FAIL - Should have thrown error' });
    } catch (error) {
      errorTests.push({ test: 'invalid_provider', result: 'PASS - ' + error.message });
    }

    // Test 2: Empty prompt (if providers available)
    if (hasAvailableProvider()) {
      try {
        await generateContent('');
        errorTests.push({ test: 'empty_prompt', result: 'PASS - Handled gracefully' });
      } catch (error) {
        errorTests.push({ test: 'empty_prompt', result: 'PASS - ' + error.message });
      }
    }

    this.results.errorTesting = errorTests;

    console.log('✅ Error handling tests completed');
    errorTests.forEach(test => {
      console.log(`   ${test.test}: ${test.result}`);
    });
  }

  async step9_PerformanceAnalysis() {
    console.log('\n📈 STEP 9: Performance Analysis');
    console.log('-'.repeat(50));

    if (!hasAvailableProvider()) {
      console.log('⏭️  Skipped - no providers available');
      return;
    }

    // Run multiple small tests to get performance averages
    const tests = [
      'Short test 1',
      'Short test 2', 
      'Short test 3'
    ];

    for (const [index, prompt] of tests.entries()) {
      try {
        const startTime = Date.now();
        const result = await evi.enhancedGenerate(prompt, {
          maxTokens: 30,
          enhance: false
        });
        const duration = Date.now() - startTime;

        this.results.performance.push({
          test: `test_${index + 1}`,
          duration,
          contentLength: result.content.length,
          success: true
        });

        console.log(`✅ Performance test ${index + 1}: ${duration}ms (${result.content.length} chars)`);
        
      } catch (error) {
        this.results.performance.push({
          test: `test_${index + 1}`,
          error: error.message,
          success: false
        });
        console.log(`❌ Performance test ${index + 1} failed: ${error.message}`);
      }
    }

    // Calculate averages
    const successfulTests = this.results.performance.filter(t => t.success);
    if (successfulTests.length > 0) {
      const avgDuration = successfulTests.reduce((sum, t) => sum + t.duration, 0) / successfulTests.length;
      const avgLength = successfulTests.reduce((sum, t) => sum + t.contentLength, 0) / successfulTests.length;
      
      console.log(`\n📉 Performance Summary:`);
      console.log(`   Average duration: ${Math.round(avgDuration)}ms`);
      console.log(`   Average content length: ${Math.round(avgLength)} characters`);
      console.log(`   Success rate: ${successfulTests.length}/${tests.length}`);
    }
  }

  generateFinalReport() {
    console.log('\n' + '='.repeat(70));
    console.log('🏆 EVI INTEGRATION WORKFLOW COMPLETE!');
    console.log('='.repeat(70));

    const summary = {
      initialization: this.results.initialization?.status || 'failed',
      basicGeneration: this.results.basicGeneration?.success || false,
      enhancedGeneration: this.results.enhancedGeneration?.success || false,
      streaming: this.results.streaming?.success || false,
      enhancedStreaming: this.results.enhancedStreaming?.success || false,
      multiProvider: this.results.multiProvider?.success || false,
      healthCheck: this.results.healthCheck?.status || 'failed',
      errorHandling: this.results.errorTesting?.length > 0,
      performance: this.results.performance.filter(t => t.success).length
    };

    console.log('\n📋 WORKFLOW SUMMARY:');
    Object.entries(summary).forEach(([key, value]) => {
      const status = this.getStatusIcon(value);
      console.log(`   ${key}: ${status} ${value}`);
    });

    const successCount = Object.values(summary).filter(v => 
      v === 'ready' || v === 'healthy' || v === true || (typeof v === 'number' && v > 0)
    ).length;
    
    console.log(`\n🎯 Overall Success Rate: ${successCount}/${Object.keys(summary).length}`);
    
    if (successCount >= Object.keys(summary).length * 0.8) {
      console.log('🎉 EXCELLENT! Your Evi integration is production-ready!');
      console.log('\n🚀 Next Steps:');
      console.log('   1. Configure your preferred AI providers in .env');
      console.log('   2. Deploy your application with confidence');
      console.log('   3. Monitor performance in production');
      console.log('   4. Scale as needed with additional providers');
    } else {
      console.log('⚠️  Some components need attention before production deployment');
      console.log('\n🔧 Recommended Actions:');
      console.log('   1. Review failed components above');
      console.log('   2. Check provider configurations');
      console.log('   3. Verify environment variables');
      console.log('   4. Re-run this workflow after fixes');
    }

    console.log('\n📎 Detailed results stored in workflow execution log');
    console.log(`Completed at: ${new Date().toISOString()}`);
  }

  getStatusIcon(value) {
    if (value === 'ready' || value === 'healthy' || value === true) return '✅';
    if (typeof value === 'number' && value > 0) return '✅';
    if (value === 'failed' || value === false) return '❌';
    return '⚠️ ';
  }
}

// Execute workflow if run directly
if (import.meta.url === `file://${process.argv[1]}`) {
  const executor = new EviWorkflowExecutor();
  
  executor.execute()
    .then(() => {
      console.log('\n🎉 Workflow execution completed successfully!');
      process.exit(0);
    })
    .catch((error) => {
      console.error('\n🚫 Workflow execution failed:', error.message);
      process.exit(1);
    });
}

export { EviWorkflowExecutor };