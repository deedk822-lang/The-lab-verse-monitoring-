import { BaseProvider } from './BaseProvider.js';
import axios from 'axios';
import { logger } from '../../utils/logger.js';

export class LocalAIProvider extends BaseProvider {
  constructor(config) {
    super(config);
    this.isLocal = true;
  }

  async generateText(prompt, options = {}) {
    const {
      model = this.config.models.text[0],
      maxTokens = 4000,
      temperature = 0.7,
      stream = false
    } = options;

    this.validateModel(model, 'text');

    try {
      const response = await this.makeRequest('/v1/chat/completions', {
        model,
        messages: [{ role: 'user', content: prompt }],
        max_tokens: Math.min(maxTokens, this.maxTokens),
        temperature,
        stream
      });

      const content = response.choices[0].message.content;
      const usage = response.usage || { total_tokens: 0 };
      const cost = this.calculateCost(usage.total_tokens);

      return {
        content,
        usage,
        cost,
        model,
        provider: 'localai'
      };
    } catch (error) {
      logger.error('LocalAI text generation failed:', error);
      throw error;
    }
  }

  async generateImage(prompt, options = {}) {
    const {
      model = this.config.models.image[0],
      size = '1024x1024',
      steps = 20,
      guidance = 7.5
    } = options;

    this.validateModel(model, 'image');

    try {
      const response = await this.makeRequest('/v1/images/generations', {
        model,
        prompt,
        size,
        n: 1,
        response_format: 'url'
      });

      const images = response.data.map(img => ({
        url: img.url,
        prompt: img.revised_prompt || prompt
      }));

      return {
        images,
        model,
        provider: 'localai'
      };
    } catch (error) {
      logger.error('LocalAI image generation failed:', error);
      throw error;
    }
  }

  async generateAudio(prompt, options = {}) {
    const {
      model = 'tts',
      voice = 'alloy',
      format = 'mp3'
    } = options;

    try {
      const response = await this.makeRequest('/v1/audio/speech', {
        model,
        input: prompt,
        voice,
        response_format: format
      });

      // LocalAI returns audio as base64
      const base64Audio = response.audio;

      return {
        audio: base64Audio,
        format,
        model,
        provider: 'localai'
      };
    } catch (error) {
      logger.error('LocalAI audio generation failed:', error);
      throw error;
    }
  }

  async analyzeContent(content, options = {}) {
    const {
      model = this.config.models.text[0],
      type = 'text'
    } = options;

    try {
      let prompt;
      if (type === 'image') {
        prompt = 'Analyze this image and provide a detailed description of its content, style, and composition.';
      } else if (type === 'video') {
        prompt = 'Analyze this video content and provide insights about its key elements and message.';
      } else {
        prompt = 'Analyze the following content and provide insights about its structure, tone, and effectiveness.';
      }

      const response = await this.generateText(`${prompt}\n\nContent: ${content}`, { model });

      return {
        analysis: response.content,
        model,
        provider: 'localai'
      };
    } catch (error) {
      logger.error('LocalAI content analysis failed:', error);
      throw error;
    }
  }

  async getModels() {
    try {
      const response = await this.client.get('/v1/models');
      return response.data.data;
    } catch (error) {
      logger.error('Failed to fetch LocalAI models:', error);
      return [];
    }
  }

  async downloadModel(modelName) {
    try {
      const response = await this.makeRequest('/v1/models', {
        name: modelName,
        action: 'download'
      });
      
      return {
        success: true,
        model: modelName,
        message: 'Model download initiated'
      };
    } catch (error) {
      logger.error(`Failed to download model ${modelName}:`, error);
      throw error;
    }
  }

  async getModelStatus(modelName) {
    try {
      const response = await this.client.get(`/v1/models/${modelName}`);
      return response.data;
    } catch (error) {
      logger.error(`Failed to get status for model ${modelName}:`, error);
      return { status: 'unknown' };
    }
  }

  async getQuote(model) {
    // LocalAI is free
    return 0;
  }
}