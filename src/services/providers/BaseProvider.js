import axios from 'axios';
import { logger } from '../../utils/logger.js';

export class BaseProvider {
  constructor(config) {
    this.config = config;
    this.name = config.name;
    this.baseUrl = config.baseUrl;
    this.apiKey = config.apiKey;
    this.maxTokens = config.maxTokens;
    this.costPerToken = config.costPerToken;
    
    this.client = axios.create({
      baseURL: this.baseUrl,
      timeout: 30000,
      headers: {
        'Authorization': `Bearer ${this.apiKey}`,
        'Content-Type': 'application/json'
      }
    });
  }

  async makeRequest(endpoint, data, options = {}) {
    try {
      const response = await this.client.post(endpoint, data, {
        ...options,
        headers: {
          ...this.client.defaults.headers,
          ...options.headers
        }
      });
      
      return response.data;
    } catch (error) {
      logger.error(`API request failed for ${this.name}:`, {
        endpoint,
        error: error.response?.data || error.message,
        status: error.response?.status
      });
      throw new Error(`API request failed: ${error.response?.data?.error?.message || error.message}`);
    }
  }

  calculateCost(tokens) {
    return tokens * this.costPerToken;
  }

  validateModel(model, type) {
    if (!this.config.models[type]?.includes(model)) {
      throw new Error(`Model ${model} not supported for ${type} generation`);
    }
  }

  async generateText(prompt, options = {}) {
    throw new Error('generateText method must be implemented by subclass');
  }

  async generateImage(prompt, options = {}) {
    throw new Error('generateImage method must be implemented by subclass');
  }

  async generateVideo(prompt, options = {}) {
    throw new Error('generateVideo method must be implemented by subclass');
  }

  async generateAudio(prompt, options = {}) {
    throw new Error('generateAudio method must be implemented by subclass');
  }

  async analyzeContent(content, options = {}) {
    throw new Error('analyzeContent method must be implemented by subclass');
  }
}