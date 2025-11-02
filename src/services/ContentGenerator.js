// src/services/ContentGenerator.js
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
        options = {}
      } = request;

      logger.info('Starting content generation:', { topic, audience, tone });

      const prompt = this.buildPrompt({
        topic,
        audience,
        tone,
        length,
        keywords,
        optimizeForSocial: options.optimizeForSocial,
        optimizeForEmail: options.optimizeForEmail,
        platforms: options.platforms
      });

      const content = await generateContent(prompt, {
        maxTokens: this.getMaxTokens(length),
        temperature: 0.7,
        timeout: 30000
      });

      if (!content || content.trim().length === 0) {
        throw new Error('Generated content is empty');
      }

      logger.info('Content generated successfully:', {
        contentLength: content.length,
        topic
      });

      return {
        success: true,
        content,
        metadata: {
          title: topic,
          generatedAt: new Date().toISOString(),
          wordCount: content.split(/\s+/).length,
          characterCount: content.length
        },
        provider: 'mistral-local'
      };

    } catch (error) {
      logger.error('Content generation failed:', {
        error: error.message,
        topic: request.topic
      });

      return {
        success: false,
        error: error.message
      };
    }
  }

  buildPrompt({ topic, audience, tone, length, keywords, optimizeForSocial, optimizeForEmail, platforms }) {
    let prompt = `Create ${this.getLengthDescription(length)} content about: ${topic}\n\n`;
    prompt += `Target audience: ${audience}\n`;
    prompt += `Writing tone: ${tone}\n`;
    
    if (keywords && keywords.length > 0) {
      prompt += `Important keywords to include: ${keywords.join(', ')}\n`;
    }
    
    if (optimizeForSocial && platforms && platforms.length > 0) {
      prompt += `\nOptimize for social media platforms: ${platforms.join(', ')}\n`;
      prompt += `Requirements:\n`;
      prompt += `- Start with an attention-grabbing hook\n`;
      prompt += `- Use clear, concise language\n`;
      prompt += `- Include relevant hashtags if appropriate\n`;
      prompt += `- End with a call-to-action\n`;
    }
    
    if (optimizeForEmail) {
      prompt += `\nAlso format appropriately for email newsletter distribution.\n`;
    }
    
    prompt += `\nGenerate engaging, well-structured content now:`;
    
    return prompt;
  }

  getLengthDescription(length) {
    const descriptions = {
      short: 'brief (150-250 words)',
      medium: 'medium-length (250-500 words)',
      long: 'comprehensive (500-1000 words)'
    };
    return descriptions[length] || descriptions.medium;
  }

  getMaxTokens(length) {
    const tokenMap = {
      short: 300,
      medium: 600,
      long: 1200
    };
    return tokenMap[length] || 600;
  }
}