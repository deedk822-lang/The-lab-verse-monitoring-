import axios from 'axios';
import { logger } from '../utils/logger.js';

class PerplexityService {
  constructor() {
    this.apiKey = process.env.PERPLEXITY_API_KEY;
    this.baseURL = 'https://api.perplexity.ai';
    this.model = process.env.PERPLEXITY_MODEL || 'llama-3.1-sonar-large-128k-online';

    if (!this.apiKey) {
      logger.warn('PERPLEXITY_API_KEY not found in environment variables');
    }
  }

  /**
   * Generate content using Perplexity AI with web search capabilities
   * @param {Object} params - Generation parameters
   * @param {string} params.prompt - The content prompt
   * @param {boolean} params.searchEnabled - Whether to use web search (default: true)
   * @param {number} params.maxTokens - Maximum tokens to generate
   * @param {number} params.temperature - Creativity level (0-1)
   * @returns {Promise<Object>} - Generation result
   */
  async generateContent(params) {
    try {
      if (!this.apiKey) {
        throw new Error('Perplexity API key not configured');
      }

      const {
        prompt,
        searchEnabled = true,
        maxTokens = 2000,
        temperature = 0.7,
        systemPrompt = 'You are a helpful AI assistant that provides accurate, well-researched content.'
      } = params;

      // Use Sonar models for web search, regular models for offline generation
      const selectedModel = searchEnabled
        ? (this.model.includes('sonar') ? this.model : 'llama-3.1-sonar-large-128k-online')
        : 'llama-3.1-8b-instruct';

      const payload = {
        model: selectedModel,
        messages: [
          {
            role: 'system',
            content: systemPrompt
          },
          {
            role: 'user',
            content: prompt
          }
        ],
        max_tokens: maxTokens,
        temperature: temperature,
        top_p: 0.9,
        search_domain_filter: searchEnabled ? ['news', 'academic', 'social'] : undefined,
        return_citations: searchEnabled,
        return_images: false
      };

      logger.info('Generating content with Perplexity:', {
        model: selectedModel,
        searchEnabled,
        promptLength: prompt.length,
        maxTokens
      });

      const response = await axios.post(`${this.baseURL}/chat/completions`, payload, {
        headers: {
          'Authorization': `Bearer ${this.apiKey}`,
          'Content-Type': 'application/json'
        },
        timeout: 60000 // 60 second timeout for web search
      });

      const generatedContent = response.data.choices[0].message.content;
      const citations = response.data.citations || [];

      logger.info('Perplexity content generated successfully:', {
        contentLength: generatedContent.length,
        citationsCount: citations.length,
        model: selectedModel,
        usage: response.data.usage
      });

      return {
        success: true,
        content: generatedContent,
        metadata: {
          model: selectedModel,
          searchEnabled,
          citations,
          usage: response.data.usage,
          timestamp: new Date().toISOString()
        },
        provider: 'perplexity'
      };

    } catch (error) {
      logger.error('Perplexity content generation failed:', {
        error: error.message,
        response: error.response?.data,
        status: error.response?.status
      });

      return {
        success: false,
        error: error.message,
        details: error.response?.data,
        provider: 'perplexity'
      };
    }
  }

  /**
   * Research a topic using Perplexity's web search capabilities
   * @param {Object} params - Research parameters
   * @param {string} params.query - Research query
   * @param {Array} params.domains - Specific domains to search
   * @param {string} params.focusArea - Specific focus area for research
   * @returns {Promise<Object>} - Research results
   */
  async researchTopic(params) {
    try {
      const { query, domains = [], focusArea = 'comprehensive' } = params;

      let researchPrompt = `Research and provide comprehensive information about: ${query}\n\n`;

      if (focusArea === 'recent') {
        researchPrompt += 'Focus on the most recent developments, news, and updates. ';
      } else if (focusArea === 'trends') {
        researchPrompt += 'Focus on current trends, market analysis, and future predictions. ';
      } else if (focusArea === 'technical') {
        researchPrompt += 'Focus on technical details, specifications, and expert analysis. ';
      }

      researchPrompt += 'Provide accurate, well-sourced information with proper citations.';

      const result = await this.generateContent({
        prompt: researchPrompt,
        searchEnabled: true,
        maxTokens: 3000,
        temperature: 0.3, // Lower temperature for factual research
        systemPrompt: 'You are a research assistant that provides accurate, well-sourced information with proper citations. Always fact-check information and provide multiple perspectives when relevant.'
      });

      if (result.success) {
        result.metadata.researchType = focusArea;
        result.metadata.domains = domains;
        result.metadata.query = query;
      }

      return result;
    } catch (error) {
      logger.error('Perplexity research failed:', error.message);
      return {
        success: false,
        error: error.message,
        provider: 'perplexity'
      };
    }
  }

  /**
   * Generate social media optimized content with current trends
   * @param {Object} params - Social content parameters
   * @param {string} params.topic - Content topic
   * @param {Array} params.platforms - Target platforms
   * @param {string} params.tone - Content tone
   * @param {boolean} params.includeTrends - Whether to include current trends
   * @returns {Promise<Object>} - Social content result
   */
  async generateSocialContent(params) {
    try {
      const {
        topic,
        platforms = ['twitter', 'linkedin'],
        tone = 'professional',
        includeTrends = true,
        hashtags = true
      } = params;

      let prompt = `Create engaging social media content about: ${topic}\n\n`;
      prompt += `Target platforms: ${platforms.join(', ')}\n`;
      prompt += `Tone: ${tone}\n\n`;

      if (includeTrends) {
        prompt += 'Research current trends and news related to this topic and incorporate relevant insights. ';
      }

      prompt += 'Requirements:\n';
      prompt += '- Make it engaging and shareable\n';
      prompt += '- Keep within platform character limits\n';

      if (hashtags) {
        prompt += '- Include relevant hashtags\n';
      }

      prompt += '- Ensure accuracy and credibility\n';
      prompt += '- Adapt tone and style for the target platforms';

      const result = await this.generateContent({
        prompt,
        searchEnabled: includeTrends,
        maxTokens: 1500,
        temperature: 0.8,
        systemPrompt: `You are a social media content creator specializing in ${tone} content for ${platforms.join(' and ')}. Create engaging, platform-optimized content that drives engagement while maintaining accuracy.`
      });

      if (result.success) {
        result.metadata.platforms = platforms;
        result.metadata.tone = tone;
        result.metadata.includeTrends = includeTrends;
        result.metadata.contentType = 'social';
      }

      return result;
    } catch (error) {
      logger.error('Perplexity social content generation failed:', error.message);
      return {
        success: false,
        error: error.message,
        provider: 'perplexity'
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
        prompt: 'Hello, this is a connection test.',
        searchEnabled: false,
        maxTokens: 50,
        temperature: 0.1
      });

      return result.success;
    } catch (error) {
      logger.error('Perplexity connection test failed:', error.message);
      return false;
    }
  }

  /**
   * Get available models
   * @returns {Promise<Object>} - Available models
   */
  async getModels() {
    try {
      if (!this.apiKey) {
        throw new Error('Perplexity API key not configured');
      }

      const response = await axios.get(`${this.baseURL}/models`, {
        headers: {
          'Authorization': `Bearer ${this.apiKey}`
        }
      });

      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      logger.error('Failed to get Perplexity models:', error.message);
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Generate fact-checked content with citations
   * @param {Object} params - Fact-check parameters
   * @param {string} params.topic - Topic to fact-check and write about
   * @param {boolean} params.includeCounterpoints - Include different perspectives
   * @returns {Promise<Object>} - Fact-checked content
   */
  async generateFactCheckedContent(params) {
    try {
      const { topic, includeCounterpoints = true } = params;

      let prompt = `Research and write fact-checked content about: ${topic}\n\n`;
      prompt += 'Requirements:\n';
      prompt += '- Verify all facts with multiple reliable sources\n';
      prompt += '- Include proper citations for all claims\n';
      prompt += '- Present information objectively\n';

      if (includeCounterpoints) {
        prompt += '- Include different perspectives and viewpoints where relevant\n';
      }

      prompt += '- Clearly distinguish between facts and opinions\n';
      prompt += '- Use recent and authoritative sources';

      const result = await this.generateContent({
        prompt,
        searchEnabled: true,
        maxTokens: 2500,
        temperature: 0.2, // Very low temperature for factual accuracy
        systemPrompt: 'You are a fact-checking journalist who provides accurate, well-researched content with proper citations. Always verify information with multiple sources and present balanced viewpoints.'
      });

      if (result.success) {
        result.metadata.contentType = 'fact-checked';
        result.metadata.includeCounterpoints = includeCounterpoints;
        result.metadata.verificationLevel = 'high';
      }

      return result;
    } catch (error) {
      logger.error('Perplexity fact-checked content generation failed:', error.message);
      return {
        success: false,
        error: error.message,
        provider: 'perplexity'
      };
    }
  }
}

// Export singleton instance
export default new PerplexityService();
