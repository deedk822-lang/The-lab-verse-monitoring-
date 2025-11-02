import { BaseProvider } from './BaseProvider.js';
import { logger } from '../../utils/logger.js';
import OpenAI from 'openai';

export class LocalAIProvider extends BaseProvider {
  constructor(config) {
    super(config);
    this.client = new OpenAI({
      baseURL: this.config.baseURL,
      apiKey: this.config.apiKey,
    });
  }

  async generateText(prompt, options = {}) {
    try {
      const response = await this.client.chat.completions.create({
        model: this.config.models.text[0],
        messages: [{ role: 'user', content: prompt }],
        max_tokens: options.maxTokens,
      });
      return {
        success: true,
        content: response.choices[0].message.content,
      };
    } catch (error) {
      logger.error('LocalAI text generation failed:', error);
      throw new Error(`API request failed: ${error.message}`);
    }
  }
}