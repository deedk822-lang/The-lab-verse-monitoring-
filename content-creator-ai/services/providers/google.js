const { GoogleGenerativeAI } = require('@google/generative-ai');
const axios = require('axios');
const config = require('../../config/config');
const logger = require('../../utils/logger');
const costTracker = require('../../utils/cost-tracker');

class GoogleProvider {
  constructor() {
    this.enabled = config.providers.google.enabled;
    if (this.enabled) {
      this.genAI = new GoogleGenerativeAI(config.providers.google.apiKey);
    }
  }

  async generateText(prompt, options = {}) {
    if (!this.enabled) {
      throw new Error('Google AI provider not enabled. Please set GOOGLE_API_KEY.');
    }

    try {
      const model = this.genAI.getGenerativeModel({ 
        model: options.model || config.providers.google.models.text 
      });

      const generationConfig = {
        temperature: options.temperature || 0.7,
        topK: options.topK || 40,
        topP: options.topP || 0.95,
        maxOutputTokens: options.maxTokens || 2048,
      };

      const result = await model.generateContent({
        contents: [{ role: 'user', parts: [{ text: prompt }] }],
        generationConfig
      });

      const response = result.response;
      const text = response.text();

      // Track costs
      const inputTokens = prompt.split(/\s+/).length * 1.3; // Rough estimate
      const outputTokens = text.split(/\s+/).length * 1.3;
      const cost = costTracker.calculateTokenCost('google', generationConfig.model || config.providers.google.models.text, inputTokens, outputTokens);

      logger.info(`Google Gemini text generated: ${text.length} chars, cost: $${cost.toFixed(4)}`);

      return {
        text,
        usage: { inputTokens, outputTokens },
        cost
      };
    } catch (error) {
      logger.error('Google text generation error:', error);
      throw error;
    }
  }

  async performResearch(query, options = {}) {
    if (!this.enabled) {
      throw new Error('Google AI provider not enabled.');
    }

    try {
      // Use Gemini with Google Search grounding
      const model = this.genAI.getGenerativeModel({ 
        model: config.providers.google.models.text 
      });

      const searchPrompt = `Research the following topic and provide detailed, accurate information with sources:\n\n${query}\n\nProvide a comprehensive summary with key facts, statistics, and recent developments.`;

      const result = await this.generateText(searchPrompt, options);

      // If Search Engine ID is configured, also fetch Google Custom Search results
      let searchResults = null;
      if (config.providers.google.searchEngineId) {
        searchResults = await this.googleCustomSearch(query);
      }

      return {
        summary: result.text,
        searchResults: searchResults?.items || [],
        sources: this.extractSources(result.text),
        usage: result.usage,
        cost: result.cost
      };
    } catch (error) {
      logger.error('Google research error:', error);
      throw error;
    }
  }

  async googleCustomSearch(query) {
    if (!config.providers.google.searchEngineId) {
      return null;
    }

    try {
      const response = await axios.get('https://www.googleapis.com/customsearch/v1', {
        params: {
          key: config.providers.google.apiKey,
          cx: config.providers.google.searchEngineId,
          q: query,
          num: 5
        }
      });

      return response.data;
    } catch (error) {
      logger.error('Google Custom Search error:', error);
      return null;
    }
  }

  async generateImage(prompt, options = {}) {
    // Note: Imagen API requires vertex AI setup. This is a placeholder for the implementation.
    // In production, you'd use Vertex AI SDK or REST API
    logger.warn('Imagen image generation requires Vertex AI setup - using placeholder');
    
    return {
      imageUrl: 'https://placeholder.com/800x600', // Placeholder
      prompt,
      aspectRatio: options.aspectRatio || '16:9',
      cost: costTracker.calculateMediaCost('google', 'image', 1)
    };
  }

  async generateVideo(prompt, options = {}) {
    // Note: Veo API requires vertex AI setup. This is a placeholder.
    logger.warn('Veo video generation requires Vertex AI setup - using placeholder');
    
    const duration = options.duration || 10;
    
    return {
      videoUrl: 'https://placeholder.com/video.mp4', // Placeholder
      prompt,
      duration,
      aspectRatio: options.aspectRatio || '16:9',
      cost: costTracker.calculateMediaCost('google', 'video', duration)
    };
  }

  async analyzeImage(imageUrl, prompt) {
    if (!this.enabled) {
      throw new Error('Google AI provider not enabled.');
    }

    try {
      const model = this.genAI.getGenerativeModel({ 
        model: config.providers.google.models.vision 
      });

      // Fetch image data
      const imageResponse = await axios.get(imageUrl, { responseType: 'arraybuffer' });
      const imageData = Buffer.from(imageResponse.data).toString('base64');

      const result = await model.generateContent([
        { text: prompt },
        {
          inlineData: {
            mimeType: imageResponse.headers['content-type'],
            data: imageData
          }
        }
      ]);

      const response = result.response;
      const text = response.text();

      return { analysis: text };
    } catch (error) {
      logger.error('Google image analysis error:', error);
      throw error;
    }
  }

  extractSources(text) {
    // Simple source extraction - look for URLs
    const urlRegex = /(https?:\/\/[^\s]+)/g;
    const urls = text.match(urlRegex) || [];
    return [...new Set(urls)]; // Remove duplicates
  }

  isEnabled() {
    return this.enabled;
  }

  async checkHealth() {
    if (!this.enabled) {
      return { healthy: false, message: 'Google provider is not enabled' };
    }
    try {
      // A simple non-costly operation to check API key validity and connectivity
      const model = this.genAI.getGenerativeModel({ model: config.providers.google.models.text });
      await model.countTokens("test");
      return { healthy: true, message: 'Google provider is responding' };
    } catch (error) {
      logger.error('Google provider health check failed:', error);
      return { healthy: false, message: error.message };
    }
  }
}

module.exports = new GoogleProvider();
