/* eslint-env jest */
import { describe, test, expect, beforeEach } from '@jest/globals';
import { EviIntegration } from '../src/integrations/eviIntegration.js';
import { hasAvailableProvider } from '../src/config/providers.js';

describe('EviIntegration (production)', () => {
  let evi;
  const hasProvider = hasAvailableProvider();

  beforeEach(() => {
    evi = new EviIntegration({ debug: false });
  });

  describe('Initialization', () => {
    test('should create EviIntegration instance', () => {
      expect(evi).toBeInstanceOf(EviIntegration);
      expect(evi.debug).toBe(false);
      expect(evi.maxRetries).toBe(3);
      expect(evi.timeout).toBe(30000);
    });

    test('should initialize with custom options', () => {
      const customEvi = new EviIntegration({
        debug: true,
        maxRetries: 5,
        timeout: 10000
      });
      expect(customEvi.debug).toBe(true);
      expect(customEvi.maxRetries).toBe(5);
      expect(customEvi.timeout).toBe(10000);
    });
  });

  describe('enhancedGenerate', () => {
    test('should throw error when no providers available', async () => {
      if (hasProvider) {
        console.log('⏭️  Skipping - provider is available');
        return;
      }

      await expect(evi.enhancedGenerate('hello'))
        .rejects.toThrow('No AI provider available');
    });

    test('should generate content with available provider', async () => {
      if (!hasProvider) {
        console.log('⏭️  Skipping - no provider available');
        return;
      }

      const result = await evi.enhancedGenerate('Brief test message', {
        maxTokens: 50
      });

      expect(result).toBeDefined();
      expect(result.content).toBeDefined();
      expect(result.metadata).toBeDefined();
      expect(result.metadata.enhanced).toBe(true);
    }, 10000);
  });

  describe('multiProviderGenerate', () => {
    test('should throw when no providers available', async () => {
      if (hasProvider) {
        console.log('⏭️  Skipping - provider is available');
        return;
      }

      await expect(
        evi.multiProviderGenerate('hello', {
          providers: ['mistral-local', 'gpt-4']
        })
      ).rejects.toThrow('All providers failed');
    });

    test('should use multi-provider fallback', async () => {
      if (!hasProvider) {
        console.log('⏭️  Skipping - no provider available');
        return;
      }

      const result = await evi.multiProviderGenerate('Brief test', {
        maxTokens: 50
      });

      expect(result).toBeDefined();
      expect(result.content).toBeDefined();
      expect(result.providerUsed).toBeDefined();
      expect(typeof result.fallbackAttempts).toBe('number');
    }, 10000);
  });

  describe('healthCheck', () => {
    test('should return unhealthy status when no providers', async () => {
      if (hasProvider) {
        console.log('⏭️  Skipping - provider is available');
        return;
      }

      const health = await evi.healthCheck();
      expect(health.status).toBe('unhealthy');
      expect(health.error).toBeDefined();
      expect(health.providers).toBe(false);
    });

    test('should return health status with provider', async () => {
      if (!hasProvider) {
        console.log('⏭️  Skipping - no provider available');
        return;
      }

      const health = await evi.healthCheck();
      expect(health).toBeDefined();
      expect(health.status).toMatch(/healthy|unhealthy/);
      expect(health.timestamp).toBeDefined();
    }, 10000);
  });

  describe('enhancePrompt', () => {
    test('should return original prompt when enhance is false', () => {
      const result = evi.enhancePrompt('Test', { enhance: false });
      expect(result).toBe('Test');
    });

    test('should enhance prompt with context', () => {
      const enhanced = evi.enhancePrompt('Test prompt', {
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

    test('should handle partial enhancement options', () => {
      const enhanced = evi.enhancePrompt('Test', {
        enhance: true,
        context: 'Only context'
      });

      expect(enhanced).toContain('Context: Only context');
      expect(enhanced).toContain('User Request: Test');
      expect(enhanced).not.toContain('Tone:');
    });

    test('should return original prompt without enhancements', () => {
      const result = evi.enhancePrompt('Test', { enhance: true });
      expect(result).toBe('Test');
    });
  });

  describe('Configuration', () => {
    test('should have correct default configuration', () => {
      const defaultEvi = new EviIntegration();
      expect(defaultEvi.debug).toBe(false);
      expect(defaultEvi.maxRetries).toBe(3);
      expect(defaultEvi.timeout).toBe(30000);
    });

    test('should allow timeout override', () => {
      const customEvi = new EviIntegration({ timeout: 5000 });
      expect(customEvi.timeout).toBe(5000);
    });
  });

  describe('Error Handling', () => {
    test('should handle empty prompt gracefully', async () => {
      if (!hasProvider) {
        console.log('⏭️  Skipping - no provider available');
        return;
      }

      await expect(evi.enhancedGenerate('', { maxTokens: 10 }))
        .rejects.toThrow();
    }, 10000);

    test('should handle options without enhance flag', () => {
      const result = evi.enhancePrompt('Test', {});
      expect(result).toBe('Test');
    });
  });
});
