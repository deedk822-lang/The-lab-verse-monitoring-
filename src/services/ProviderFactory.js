import { OpenAIProvider } from './providers/OpenAIProvider.js';
import { GoogleProvider } from './providers/GoogleProvider.js';
import { LocalAIProvider } from './providers/LocalAIProvider.js';
import { ZAIProvider } from './providers/ZAIProvider.js';
import { getProviderConfig, PROVIDERS } from '../config/providers.js';
import { logger } from '../utils/logger.js';

export class ProviderFactory {
  static providers = new Map();

  static getProvider(providerType) {
    if (this.providers.has(providerType)) {
      return this.providers.get(providerType);
    }

    try {
      const config = getProviderConfig(providerType);
      let provider;

      switch (providerType) {
        case PROVIDERS.OPENAI:
          provider = new OpenAIProvider(config);
          break;
        case PROVIDERS.GOOGLE:
          provider = new GoogleProvider(config);
          break;
        case PROVIDERS.LOCALAI:
          provider = new LocalAIProvider(config);
          break;
        case PROVIDERS.ZAI:
          provider = new ZAIProvider(config);
          break;
        default:
          throw new Error(`Unknown provider type: ${providerType}`);
      }

      this.providers.set(providerType, provider);
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
    
    for (const providerType of Object.values(PROVIDERS)) {
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
    this.providers.clear();
    logger.info('Provider cache cleared');
  }
}