import { generateContent } from './contentGenerator.js';
import { logger } from '../utils/logger.js';

export class ContentGenerator {
  async generateContent(request) {
    try {
      const {
        topic,
        audience,
        tone,
        length,
        keywords = [],
        options = {},
      } = request;

      const prompt = this.buildPrompt({
        topic,
        audience,
        tone,
        length,
        keywords,
        optimizeForSocial: options.optimizeForSocial,
        optimizeForEmail: options.optimizeForEmail,
        platforms: options.platforms,
      });

      const content = await generateContent(prompt, {
        maxTokens: this.getMaxTokens(length),
        temperature: 0.7,
      });

      return {
        success: true,
        content,
        metadata: {
          title: topic,
          generatedAt: new Date().toISOString(),
        },
      };

    } catch (error) {
      logger.error('Content generation failed:', error);
      return {
        success: false,
        error: error.message,
      };
    }
  }

  buildPrompt({ topic, audience, tone, length, keywords, optimizeForSocial, platforms }) {
    let prompt = `Write ${length || 'medium'} length content about: ${topic}\n`;
    prompt += `Target audience: ${audience}\n`;
    prompt += `Tone: ${tone}\n`;

    if (keywords.length > 0) {
      prompt += `Keywords: ${keywords.join(', ')}\n`;
    }

    if (optimizeForSocial && platforms) {
      prompt += `Optimize for: ${platforms.join(', ')}\n`;
      prompt += 'Make it engaging with hooks and calls-to-action.\n';
    }

    prompt += '\nGenerate the content now:';

    return prompt;
  }

  getMaxTokens(length) {
    const map = {
      short: 250,
      medium: 500,
      long: 1000,
    };
    return map[length] || 500;
  }
}
