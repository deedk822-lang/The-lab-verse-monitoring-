// src/integrations/eviIntegration.js
// Evi Integration for Enhanced AI Capabilities

import { generateContent, streamContent } from '../services/contentGenerator.js';
import { getActiveProvider, hasAvailableProvider } from '../config/providers.js';
import { httpReq, tokenCounter, errorCounter } from '../metrics.js';

/**
 * Evi Integration Class
 * Provides enhanced AI capabilities through the Manus MCP connection
 */
export class EviIntegration {
  constructor(options = {}) {
    this.debug = options.debug || false;
    this.maxRetries = options.maxRetries || 3;
    this.timeout = options.timeout || 30000;
  }

  /**
   * Initialize Evi connection and verify providers
   */
  async initialize() {
    console.log('🤖 Initializing Evi Integration...');

    if (!hasAvailableProvider()) {
      throw new Error('No AI providers available for Evi integration');
    }

    const provider = getActiveProvider();
    console.log('✅ Evi Integration ready with provider:', provider);

    return {
      status: 'ready',
      provider: provider,
      capabilities: [
        'content_generation',
        'streaming_response',
        'multi_provider_fallback',
        'error_handling',
      ],
    };
  }

  /**
   * Enhanced content generation with Evi capabilities
   */
  async enhancedGenerate(prompt, options = {}) {
    const enhancedPrompt = this.enhancePrompt(prompt, options);

    try {
      const result = await generateContent(enhancedPrompt, {
        maxTokens: options.maxTokens || 1000,
        temperature: options.temperature || 0.8,
        timeout: this.timeout,
        provider: options.provider,
      });

      return {
        content: result,
        metadata: {
          provider: options.provider || 'auto-selected',
          tokens: result.length,
          timestamp: new Date().toISOString(),
          enhanced: true,
        },
      };

    } catch (error) {
      console.error('❌ Enhanced generation failed:', error.message);
      throw error;
    }
  }

  /**
   * Streaming with Evi enhancements
   */
  async* enhancedStream(prompt, options = {}) {
    const enhancedPrompt = this.enhancePrompt(prompt, options);
    let chunkCount = 0;
    let totalContent = '';

    try {
      for await (const chunk of streamContent(enhancedPrompt, options)) {
        chunkCount++;
        totalContent += chunk;

        yield {
          chunk,
          metadata: {
            chunkIndex: chunkCount,
            totalLength: totalContent.length,
            timestamp: new Date().toISOString(),
          },
        };
      }

      // Final summary chunk
      yield {
        summary: {
          totalChunks: chunkCount,
          totalLength: totalContent.length,
          completed: true,
        },
      };

    } catch (error) {
      console.error('❌ Enhanced streaming failed:', error.message);
      throw error;
    }
  }

  /**
   * Multi-provider workflow with intelligent fallback
   */
  async multiProviderGenerate(prompt, options = {}) {
    const providers = ['gpt-4', 'groq-llama', 'perplexity', 'claude-sonnet', 'gemini-pro', 'mistral'];
    let lastError = null;

    for (const provider of providers) {
      const end = httpReq.startTimer({ provider: provider, model: 'default' });
      try {
        console.log(`🔄 Attempting with provider: ${provider}`);

        const result = await this.enhancedGenerate(prompt, {
          ...options,
          provider,
        });

        end({ status: 'success' });
        tokenCounter.inc({ provider: provider, model: 'default' }, Math.ceil(result.content.length / 4));
        console.log(`✅ Success with provider: ${provider}`);
        return {
          ...result,
          providerUsed: provider,
          fallbackAttempts: providers.indexOf(provider),
        };

      } catch (error) {
        end({ status: 'error' });
        errorCounter.inc({ provider: provider, code: error.status || 500 });
        console.warn(`⚠️  Provider ${provider} failed: ${error.message}`);
        lastError = error;
        continue;
      }
    }

    throw new Error(`All providers failed. Last error: ${lastError?.message}`);
  }

  /**
   * Enhance prompts with Evi context and capabilities
   */
  enhancePrompt(prompt, options = {}) {
    if (!options.enhance) {
      return prompt;
    }

    const enhancements = [];

    if (options.context) {
      enhancements.push(`Context: ${options.context}`);
    }

    if (options.tone) {
      enhancements.push(`Tone: ${options.tone}`);
    }

    if (options.format) {
      enhancements.push(`Format: ${options.format}`);
    }

    const enhancedPrompt = enhancements.length > 0
      ? `${enhancements.join('\n')}\n\nUser Request: ${prompt}`
      : prompt;

    if (this.debug) {
      console.log('🔍 Enhanced prompt:', enhancedPrompt);
    }

    return enhancedPrompt;
  }

  /**
   * Health check for Evi integration
   */
  async healthCheck() {
    try {
      const testResult = await generateContent('Test message: respond with "OK"', {
        maxTokens: 10,
        timeout: 5000,
      });

      return {
        status: 'healthy',
        response: testResult,
        timestamp: new Date().toISOString(),
        providers: hasAvailableProvider(),
      };

    } catch (error) {
      return {
        status: 'unhealthy',
        error: error.message,
        timestamp: new Date().toISOString(),
        providers: hasAvailableProvider(),
      };
    }
  }
}

// Export singleton instance
export const evi = new EviIntegration({ debug: process.env.NODE_ENV === 'development' });

export default EviIntegration;
