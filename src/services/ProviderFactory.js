import { OpenAIProvider } from './providers/OpenAIProvider.js';
import { GoogleProvider } from './providers/GoogleProvider.js';
import { LocalAIProvider } from './providers/LocalAIProvider.js';
import { ZAIProvider } from './providers/ZAIProvider.js';
import { AnthropicProvider } from './providers/AnthropicProvider.js';
import { providers } from '../config/providers.js';
import { logger } from '../utils/logger.js';

export class ProviderFactory {
  static providerInstances = new Map();

  static getProvider(providerType) {
    if (this.providerInstances.has(providerType)) {
      return this.providerInstances.get(providerType);
    }

    try {
      const config = providers[providerType];
      if (!config) {
        throw new Error(`Unknown provider type: ${providerType}`);
      }

      let provider;

      // This is a bit of a hack, we should probably have a better way to map these
      if (providerType === 'gpt-4') {
        provider = new OpenAIProvider(config);
      } else if (providerType === 'google') {
        provider = new GoogleProvider(config);
      } else if (providerType === 'mistral-local') {
        provider = new LocalAIProvider(config);
      } else if (providerType === 'zai') {
        provider = new ZAIProvider(config);
      } else if (providerType === 'claude-sonnet') {
        provider = new AnthropicProvider(config);
      } else {
        throw new Error(`No provider class found for type: ${providerType}`);
      }

      this.providerInstances.set(providerType, provider);
      logger.info(`Initialized ${providerType} provider`);
      return provider;
    } catch (error) {
      logger.error(`Failed to initialize ${providerType} provider:`, error);
      throw error;
    }
  }

  static async testProvider(providerType) {
    try {
      const provider = this.getProvider(providerType);
      
      // Test with a simple prompt
      const result = await provider.generateText('Hello, this is a test.', {
        maxTokens: 10
      });

      return {
        success: true,
        provider: providerType,
        response: result.content.substring(0, 100) + '...'
      };
    } catch (error) {
      return {
        success: false,
        provider: providerType,
        error: error.message
      };
    }
  }

  static async testAllProviders() {
    const results = {};
    
    for (const providerType of Object.keys(providers)) {
      try {
        results[providerType] = await this.testProvider(providerType);
      } catch (error) {
        results[providerType] = {
          success: false,
          provider: providerType,
          error: error.message
        };
      }
    }

    return results;
  }

  static clearCache() {
    this.providerInstances.clear();
    logger.info('Provider cache cleared');
  }
}