// test/evi-integration.test.js
// Enhanced testing for Evi integration capabilities

import { EviIntegration, evi } from '../src/integrations/eviIntegration.js';
import { hasAvailableProvider } from '../src/config/providers.js';

describe('Evi Integration Tests', () => {
  let eviInstance;

  beforeAll(async () => {
    if (!hasAvailableProvider()) {
      console.warn('⚠️  No AI providers configured - Evi tests will be skipped');
      return;
    }

    eviInstance = new EviIntegration({ debug: true });
    await eviInstance.initialize();
  });

  describe('Initialization', () => {
    test('should initialize Evi integration successfully', async () => {
      if (!hasAvailableProvider()) {
        console.log('⏭️  Skipping - no provider available');
        return;
      }

      const result = await eviInstance.initialize();
      
      expect(result.status).toBe('ready');
      expect(result.capabilities).toContain('content_generation');
      expect(result.capabilities).toContain('streaming_response');
      expect(result.provider).toBeTruthy();
    });

    test('should use singleton instance correctly', () => {
      expect(evi).toBeInstanceOf(EviIntegration);
    });
  });

  describe('Enhanced Content Generation', () => {
    test('should generate enhanced content with metadata', async () => {
      if (!hasAvailableProvider()) {
        console.log('⏭️  Skipping - no provider available');
        return;
      }

      const result = await eviInstance.enhancedGenerate(
        'Write a brief message about AI testing',
        {
          maxTokens: 100,
          enhance: true,
          context: 'Software testing environment',
          tone: 'technical'
        }
      );

      expect(result.content).toBeTruthy();
      expect(result.metadata).toBeTruthy();
      expect(result.metadata.enhanced).toBe(true);
      expect(result.metadata.timestamp).toBeTruthy();
      expect(typeof result.metadata.tokens).toBe('number');
    }, 20000);

    test('should handle prompt enhancement', () => {
      const enhanced = eviInstance.enhancePrompt('Test prompt', {
        enhance: true,
        context: 'Testing context',
        tone: 'professional',
        format: 'brief'
      });

      expect(enhanced).toContain('Context: Testing context');
      expect(enhanced).toContain('Tone: professional');
      expect(enhanced).toContain('Format: brief');
      expect(enhanced).toContain('User Request: Test prompt');
    });
  });

  describe('Enhanced Streaming', () => {
    test('should stream content with enhanced metadata', async () => {
      if (!hasAvailableProvider()) {
        console.log('⏭️  Skipping - no provider available');
        return;
      }

      const chunks = [];
      const stream = eviInstance.enhancedStream(
        'Count to 3 with explanations',
        {
          maxTokens: 100,
          enhance: true,
          context: 'Educational counting'
        }
      );

      for await (const chunk of stream) {
        chunks.push(chunk);
        
        if (chunk.chunk) {
          expect(chunk.metadata).toBeTruthy();
          expect(chunk.metadata.chunkIndex).toBeTruthy();
          expect(chunk.metadata.timestamp).toBeTruthy();
        }
        
        if (chunk.summary) {
          expect(chunk.summary.completed).toBe(true);
          expect(chunk.summary.totalChunks).toBeGreaterThan(0);
        }
      }

      expect(chunks.length).toBeGreaterThan(0);
      expect(chunks[chunks.length - 1].summary).toBeTruthy();
    }, 25000);
  });

  describe('Multi-Provider Workflow', () => {
    test('should handle multi-provider fallback', async () => {
      if (!hasAvailableProvider()) {
        console.log('⏭️  Skipping - no provider available');
        return;
      }

      const result = await eviInstance.multiProviderGenerate(
        'Simple test message',
        { maxTokens: 50 }
      );

      expect(result.content).toBeTruthy();
      expect(result.providerUsed).toBeTruthy();
      expect(typeof result.fallbackAttempts).toBe('number');
      expect(result.fallbackAttempts).toBeGreaterThanOrEqual(0);
    }, 30000);

    test('should handle all providers failing gracefully', async () => {
      if (!hasAvailableProvider()) {
        console.log('⏭️  Skipping - no provider available');
        return;
      }

      // Mock all providers to fail by using invalid prompt
      await expect(
        eviInstance.multiProviderGenerate('', { maxTokens: 1 })
      ).rejects.toThrow('All providers failed');
    }, 15000);
  });

  describe('Health Monitoring', () => {
    test('should perform health check successfully', async () => {
      if (!hasAvailableProvider()) {
        console.log('⏭️  Skipping - no provider available');
        return;
      }

      const health = await eviInstance.healthCheck();
      
      expect(health.status).toBeTruthy();
      expect(health.timestamp).toBeTruthy();
      expect(typeof health.providers).toBe('boolean');
      
      if (health.status === 'healthy') {
        expect(health.response).toBeTruthy();
      } else {
        expect(health.error).toBeTruthy();
      }
    }, 10000);
  });

  describe('Error Handling', () => {
    test('should handle initialization without providers', async () => {
      const testEvi = new EviIntegration();
      
      // Temporarily mock hasAvailableProvider to return false
      const originalHasProvider = hasAvailableProvider;
      jest.spyOn({ hasAvailableProvider }, 'hasAvailableProvider')
           .mockReturnValue(false);

      await expect(testEvi.initialize())
        .rejects.toThrow('No AI providers available');

      // Restore original function
      hasAvailableProvider.mockRestore?.();
    });

    test('should handle invalid enhancement options', () => {
      const result = eviInstance.enhancePrompt('Test', { enhance: false });
      expect(result).toBe('Test');
    });
  });

  describe('Performance Metrics', () => {
    test('should track generation performance', async () => {
      if (!hasAvailableProvider()) {
        console.log('⏭️  Skipping - no provider available');
        return;
      }

      const startTime = Date.now();
      const result = await eviInstance.enhancedGenerate(
        'Brief test message',
        { maxTokens: 50 }
      );
      const duration = Date.now() - startTime;

      expect(duration).toBeLessThan(30000); // Should complete within 30s
      expect(result.metadata.tokens).toBeGreaterThan(0);
      
      console.log(`📈 Generation completed in ${duration}ms`);
    }, 35000);
  });
});