import axios from 'axios';
import { logger } from '../utils/logger.js';

class ManusService {
  constructor() {
    this.apiKey = process.env.MANUS_API_KEY;
    this.baseURL = process.env.MANUS_BASE_URL || 'https://api.manus.ai/v1';
    this.model = process.env.MANUS_MODEL || 'manus-creative-v1';

    if (!this.apiKey) {
      logger.warn('MANUS_API_KEY not found in environment variables');
    }
  }

  /**
   * Generate creative content using Manus AI
   * @param {Object} params - Generation parameters
   * @param {string} params.prompt - Content prompt
   * @param {string} params.contentType - Type of content (article, story, script, etc.)
   * @param {string} params.style - Writing style
   * @param {number} params.creativity - Creativity level (0-1)
   * @param {number} params.length - Target length
   * @returns {Promise<Object>} - Generation result
   */
  async generateContent(params) {
    try {
      if (!this.apiKey) {
        throw new Error('Manus AI API key not configured');
      }

      const {
        prompt,
        contentType = 'article',
        style = 'professional',
        creativity = 0.8,
        length = 'medium',
        audience = 'general',
        tone = 'engaging'
      } = params;

      const payload = {
        model: this.model,
        prompt,
        parameters: {
          content_type: contentType,
          writing_style: style,
          creativity_level: creativity,
          target_length: length,
          target_audience: audience,
          tone,
          enhance_readability: true,
          optimize_engagement: true
        },
        max_tokens: this.getMaxTokensForLength(length),
        temperature: creativity
      };

      logger.info('Generating content with Manus AI:', {
        contentType,
        style,
        creativity,
        length,
        promptLength: prompt.length
      });

      const response = await axios.post(`${this.baseURL}/generate`, payload, {
        headers: {
          'Authorization': `Bearer ${this.apiKey}`,
          'Content-Type': 'application/json'
        },
        timeout: 90000 // 90 second timeout for creative generation
      });

      const result = response.data;
      const generatedContent = result.content || result.text || result.output;

      logger.info('Manus AI content generated successfully:', {
        contentLength: generatedContent.length,
        contentType,
        style,
        readabilityScore: result.metrics?.readability_score,
        engagementScore: result.metrics?.engagement_score
      });

      return {
        success: true,
        content: generatedContent,
        metadata: {
          model: this.model,
          contentType,
          style,
          creativity,
          metrics: result.metrics || {},
          suggestions: result.suggestions || [],
          timestamp: new Date().toISOString()
        },
        provider: 'manus'
      };

    } catch (error) {
      logger.error('Manus AI content generation failed:', {
        error: error.message,
        response: error.response?.data,
        status: error.response?.status
      });

      return {
        success: false,
        error: error.message,
        details: error.response?.data,
        provider: 'manus'
      };
    }
  }

  /**
   * Optimize existing content for better engagement
   * @param {Object} params - Optimization parameters
   * @param {string} params.content - Original content to optimize
   * @param {Array} params.platforms - Target platforms
   * @param {string} params.optimizeFor - What to optimize for (engagement, readability, seo)
   * @returns {Promise<Object>} - Optimization result
   */
  async optimizeContent(params) {
    try {
      if (!this.apiKey) {
        throw new Error('Manus AI API key not configured');
      }

      const {
        content,
        platforms = ['social'],
        optimizeFor = 'engagement',
        targetAudience = 'general',
        preserveLength = false
      } = params;

      const payload = {
        model: this.model,
        content,
        optimization: {
          target_platforms: platforms,
          optimize_for: optimizeFor,
          target_audience: targetAudience,
          preserve_original_length: preserveLength,
          enhance_readability: true,
          add_hooks: platforms.includes('social'),
          improve_flow: true
        }
      };

      logger.info('Optimizing content with Manus AI:', {
        originalLength: content.length,
        platforms,
        optimizeFor,
        preserveLength
      });

      const response = await axios.post(`${this.baseURL}/optimize`, payload, {
        headers: {
          'Authorization': `Bearer ${this.apiKey}`,
          'Content-Type': 'application/json'
        },
        timeout: 60000
      });

      const result = response.data;
      const optimizedContent = result.optimized_content || result.content;

      logger.info('Manus AI content optimized successfully:', {
        originalLength: content.length,
        optimizedLength: optimizedContent.length,
        improvementScore: result.metrics?.improvement_score,
        changes: result.changes?.length || 0
      });

      return {
        success: true,
        content: optimizedContent,
        originalContent: content,
        metadata: {
          optimizeFor,
          platforms,
          metrics: result.metrics || {},
          changes: result.changes || [],
          suggestions: result.suggestions || [],
          timestamp: new Date().toISOString()
        },
        provider: 'manus'
      };

    } catch (error) {
      logger.error('Manus AI content optimization failed:', {
        error: error.message,
        response: error.response?.data,
        status: error.response?.status
      });

      return {
        success: false,
        error: error.message,
        details: error.response?.data,
        provider: 'manus'
      };
    }
  }

  /**
   * Generate creative social media content
   * @param {Object} params - Social content parameters
   * @param {string} params.topic - Content topic
   * @param {Array} params.platforms - Target platforms
   * @param {string} params.brand_voice - Brand voice/style
   * @param {boolean} params.includeHashtags - Include hashtags
   * @returns {Promise<Object>} - Social content result
   */
  async generateSocialContent(params) {
    try {
      const {
        topic,
        platforms = ['twitter', 'linkedin'],
        brandVoice = 'professional',
        includeHashtags = true,
        includeEmojis = true,
        callToAction = true,
        multiVariant = false
      } = params;

      let prompt = `Create engaging social media content about: ${topic}\n\n`;
      prompt += `Target platforms: ${platforms.join(', ')}\n`;
      prompt += `Brand voice: ${brandVoice}\n\n`;
      prompt += 'Requirements:\n';

      if (includeHashtags) {
        prompt += '- Include relevant and trending hashtags\n';
      }
      if (includeEmojis) {
        prompt += '- Use appropriate emojis to enhance engagement\n';
      }
      if (callToAction) {
        prompt += '- Include a compelling call-to-action\n';
      }

      prompt += '- Optimize for each platform\'s best practices\n';
      prompt += '- Make it shareable and engaging\n';
      prompt += '- Ensure brand consistency';

      const result = await this.generateContent({
        prompt,
        contentType: 'social_media',
        style: brandVoice,
        creativity: 0.9,
        length: 'short',
        audience: 'social_media_users',
        tone: 'engaging'
      });

      if (result.success && multiVariant) {
        // Generate additional variants
        const variants = [];
        for (let i = 0; i < 2; i++) {
          const variant = await this.generateContent({
            prompt: prompt + '\n\nCreate a different variation with a fresh approach.',
            contentType: 'social_media',
            style: brandVoice,
            creativity: 0.9,
            length: 'short',
            audience: 'social_media_users',
            tone: 'engaging'
          });
          if (variant.success) {
            variants.push(variant.content);
          }
        }
        result.metadata.variants = variants;
      }

      if (result.success) {
        result.metadata.platforms = platforms;
        result.metadata.brandVoice = brandVoice;
        result.metadata.features = {
          hashtags: includeHashtags,
          emojis: includeEmojis,
          callToAction,
          multiVariant
        };
      }

      return result;
    } catch (error) {
      logger.error('Manus AI social content generation failed:', error.message);
      return {
        success: false,
        error: error.message,
        provider: 'manus'
      };
    }
  }

  /**
   * Generate email content with persuasive copy
   * @param {Object} params - Email content parameters
   * @param {string} params.purpose - Email purpose (newsletter, promotion, etc.)
   * @param {string} params.subject - Email subject
   * @param {string} params.audience - Target audience
   * @param {string} params.tone - Email tone
   * @returns {Promise<Object>} - Email content result
   */
  async generateEmailContent(params) {
    try {
      const {
        purpose = 'newsletter',
        subject,
        audience = 'subscribers',
        tone = 'friendly',
        includePersonalization = true,
        length = 'medium'
      } = params;

      let prompt = `Create compelling email content for: ${purpose}\n\n`;
      if (subject) {
        prompt += `Subject: ${subject}\n`;
      }
      prompt += `Target audience: ${audience}\n`;
      prompt += `Tone: ${tone}\n\n`;
      prompt += 'Requirements:\n';
      prompt += '- Create engaging subject line if not provided\n';
      prompt += '- Write compelling opening that hooks the reader\n';
      prompt += '- Structure content with clear sections\n';
      prompt += '- Include clear call-to-action\n';

      if (includePersonalization) {
        prompt += '- Add personalization elements\n';
      }

      prompt += '- Optimize for email deliverability\n';
      prompt += '- Make it mobile-friendly';

      const result = await this.generateContent({
        prompt,
        contentType: 'email',
        style: tone,
        creativity: 0.7,
        length,
        audience,
        tone
      });

      if (result.success) {
        result.metadata.purpose = purpose;
        result.metadata.emailFeatures = {
          personalization: includePersonalization,
          mobileOptimized: true,
          deliverabilityOptimized: true
        };
      }

      return result;
    } catch (error) {
      logger.error('Manus AI email content generation failed:', error.message);
      return {
        success: false,
        error: error.message,
        provider: 'manus'
      };
    }
  }

  /**
   * Test the API connection
   * @returns {Promise<boolean>} - Connection status
   */
  async testConnection() {
    try {
      if (!this.apiKey) {
        return false;
      }

      const result = await this.generateContent({
        prompt: 'Write a brief test message.',
        contentType: 'test',
        style: 'simple',
        creativity: 0.1,
        length: 'short'
      });

      return result.success;
    } catch (error) {
      logger.error('Manus AI connection test failed:', error.message);
      return false;
    }
  }

  /**
   * Get content analysis and suggestions
   * @param {Object} params - Analysis parameters
   * @param {string} params.content - Content to analyze
   * @param {string} params.purpose - Content purpose
   * @returns {Promise<Object>} - Analysis result
   */
  async analyzeContent(params) {
    try {
      if (!this.apiKey) {
        throw new Error('Manus AI API key not configured');
      }

      const { content, purpose = 'general' } = params;

      const payload = {
        content,
        analysis_type: 'comprehensive',
        purpose,
        metrics: ['readability', 'engagement', 'sentiment', 'structure']
      };

      const response = await axios.post(`${this.baseURL}/analyze`, payload, {
        headers: {
          'Authorization': `Bearer ${this.apiKey}`,
          'Content-Type': 'application/json'
        },
        timeout: 30000
      });

      return {
        success: true,
        analysis: response.data,
        provider: 'manus'
      };
    } catch (error) {
      logger.error('Manus AI content analysis failed:', error.message);
      return {
        success: false,
        error: error.message,
        provider: 'manus'
      };
    }
  }

  /**
   * Get max tokens based on length setting
   * @param {string} length - Length setting
   * @returns {number} - Max tokens
   */
  getMaxTokensForLength(length) {
    const lengthMap = {
      'short': 500,
      'medium': 1500,
      'long': 3000,
      'very_long': 5000
    };

    return lengthMap[length] || lengthMap['medium'];
  }
}

// Export singleton instance
export default new ManusService();