import { BaseProvider } from './BaseProvider.js';
import { logger } from '../../utils/logger.js';
import Anthropic from '@anthropic-ai/sdk';

export class AnthropicProvider extends BaseProvider {
  constructor(config) {
    super(config);
    this.client = new Anthropic({
      apiKey: this.config.apiKey,
    });
  }

  async generateText(prompt, options = {}) {
    try {
      const result = await this.client.completions.create({
        model: "claude-3-5-sonnet-20241022",
        prompt: `\n\nHuman: ${prompt}\n\nAssistant:`,
        max_tokens_to_sample: options.maxTokens || 300,
      });

      return {
        success: true,
        content: result.completion,
      };
    } catch (error) {
      logger.error('Anthropic text generation failed:', error);
      throw new Error(`Anthropic API request failed: ${error.message}`);
    }
  }
}