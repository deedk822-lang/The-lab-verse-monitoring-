import { MistralClient } from '@mistralai/mistralai';
import { logger } from '../utils/logger.js';

export class MistralService {
  constructor() {
    this.client = new MistralClient(process.env.MISTRAL_API_KEY);
  }

  /**
   * The Auditor: Analyzes documents/images (Tax Collector)
   * Model: pixtral-12b-2409
   */
  async analyzeImageOrDocument(prompt, imageUrl) {
    logger.info('👁️ Mistral Pixtral: Analyzing visual data...');
    try {
      const chatResponse = await this.client.chat({
        model: 'pixtral-12b-2409',
        messages: [
          {
            role: 'user',
            content: [
              { type: 'text', text: prompt },
              { type: 'image_url', imageUrl: imageUrl }
            ]
          }
        ]
      });
      return chatResponse.choices[0].message.content;
    } catch (error) {
      logger.error('❌ Pixtral analysis failed', error);
      throw error;
    }
  }

  /**
   * The Operator: Generates high-speed code (Micro-SaaS)
   * Model: codestral-latest
   */
  async generateCode(prompt, language = 'python') {
    logger.info('💻 Mistral Codestral: Generating code...');
    try {
      const chatResponse = await this.client.chat({
        model: 'codestral-latest',
        messages: [
          {
            role: 'system',
            content: `You are The Operator. Generate production-ready ${language} code. No explanations, just code.`
          },
          { role: 'user', content: prompt }
        ]
      });
      return chatResponse.choices[0].message.content;
    } catch (error) {
      logger.error('❌ Codestral generation failed', error);
      throw error;
    }
  }

  /**
   * The Visionary: Mass content generation
   * Model: mistral-large-latest
   */
  async generateCreativeContent(topic, tone) {
    try {
      const chatResponse = await this.client.chat({
        model: 'mistral-large-latest',
        messages: [
          { role: 'system', content: `You are The Visionary. Create viral content. Tone: ${tone}` },
          { role: 'user', content: `Write a post about: ${topic}` }
        ]
      });
      return chatResponse.choices[0].message.content;
    } catch (error) {
      logger.error('❌ Visionary generation failed', error);
      throw error;
    }
  }
}
