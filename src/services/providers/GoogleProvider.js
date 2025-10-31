import { BaseProvider } from './BaseProvider.js';
import { GoogleGenerativeAI } from '@google/generative-ai';
import { google } from 'googleapis';
import axios from 'axios';
import { logger } from '../../utils/logger.js';

export class GoogleProvider extends BaseProvider {
  constructor(config) {
    super(config);
    this.genAI = new GoogleGenerativeAI(this.apiKey);
    this.projectId = config.projectId;
    this.location = config.location;
    
    // Initialize Google APIs
    this.auth = new google.auth.GoogleAuth({
      keyFile: process.env.GOOGLE_KEY_FILE,
      scopes: [
        'https://www.googleapis.com/auth/cloud-platform',
        'https://www.googleapis.com/auth/youtube',
        'https://www.googleapis.com/auth/maps-platform'
      ]
    });
  }

  async generateText(prompt, options = {}) {
    const {
      model = 'gemini-1.5-pro',
      maxTokens = 4000,
      temperature = 0.7,
      thinkingMode = false
    } = options;

    this.validateModel(model, 'text');

    try {
      const genModel = this.genAI.getGenerativeModel({ 
        model,
        generationConfig: {
          maxOutputTokens: Math.min(maxTokens, this.maxTokens),
          temperature
        }
      });

      // Enable thinking mode for complex queries if supported
      if (thinkingMode && model.includes('thinking')) {
        const result = await genModel.generateContentWithThinking(prompt);
        return {
          content: result.response.text(),
          thinking: result.thinking,
          usage: { total_tokens: result.response.usageMetadata?.totalTokenCount || 0 },
          cost: this.calculateCost(result.response.usageMetadata?.totalTokenCount || 0),
          model,
          provider: 'google'
        };
      }

      const result = await genModel.generateContent(prompt);
      const response = await result.response;
      
      return {
        content: response.text(),
        usage: { total_tokens: response.usageMetadata?.totalTokenCount || 0 },
        cost: this.calculateCost(response.usageMetadata?.totalTokenCount || 0),
        model,
        provider: 'google'
      };
    } catch (error) {
      logger.error('Google text generation failed:', error);
      throw error;
    }
  }

  async generateImage(prompt, options = {}) {
    const {
      model = 'imagen-3.0-generate-001',
      aspectRatio = '1:1',
      style = 'photographic'
    } = options;

    this.validateModel(model, 'image');

    try {
      const response = await this.makeRequest(`/models/${model}:generateImage`, {
        prompt,
        config: {
          aspectRatio,
          style
        }
      });

      return {
        images: response.images.map(img => ({
          url: img.url,
          prompt: img.prompt
        })),
        model,
        provider: 'google'
      };
    } catch (error) {
      logger.error('Google image generation failed:', error);
      throw error;
    }
  }

  async generateVideo(prompt, options = {}) {
    const {
      model = 'veo-3.1-generate-001',
      duration = 5,
      aspectRatio = '16:9'
    } = options;

    this.validateModel(model, 'video');

    try {
      const response = await this.makeRequest(`/models/${model}:generateVideo`, {
        prompt,
        config: {
          duration,
          aspectRatio
        }
      });

      return {
        videos: response.videos.map(video => ({
          url: video.url,
          prompt: video.prompt,
          duration: video.duration
        })),
        model,
        provider: 'google'
      };
    } catch (error) {
      logger.error('Google video generation failed:', error);
      throw error;
    }
  }

  async generateAudio(prompt, options = {}) {
    const {
      model = 'texttospeech',
      voice = 'en-US-Wavenet-D',
      language = 'en-US'
    } = options;

    try {
      const textToSpeech = google.texttospeech({ version: 'v1', auth: this.auth });
      
      const request = {
        input: { text: prompt },
        voice: { languageCode: language, name: voice },
        audioConfig: { audioEncoding: 'MP3' }
      };

      const response = await textToSpeech.text.synthesize({ request });
      const audioContent = response.data.audioContent;
      const base64Audio = Buffer.from(audioContent, 'base64').toString('base64');

      return {
        audio: base64Audio,
        format: 'mp3',
        voice,
        language,
        provider: 'google'
      };
    } catch (error) {
      logger.error('Google audio generation failed:', error);
      throw error;
    }
  }

  async searchWeb(query, options = {}) {
    const {
      numResults = 10,
      safeSearch = 'moderate'
    } = options;

    try {
      const response = await this.makeRequest('/models/gemini-1.5-pro:searchWeb', {
        query,
        config: {
          numResults,
          safeSearch
        }
      });

      return {
        results: response.results,
        query,
        provider: 'google'
      };
    } catch (error) {
      logger.error('Google web search failed:', error);
      throw error;
    }
  }

  async getMapsData(query, options = {}) {
    const {
      type = 'place',
      radius = 5000
    } = options;

    try {
      const maps = google.maps({ version: 'v1', auth: this.auth });
      
      const response = await maps.places.nearby({
        location: query,
        radius,
        type
      });

      return {
        places: response.data.results,
        query,
        provider: 'google'
      };
    } catch (error) {
      logger.error('Google Maps search failed:', error);
      throw error;
    }
  }

  async analyzeContent(content, options = {}) {
    const {
      model = 'gemini-1.5-pro',
      type = 'text'
    } = options;

    try {
      const genModel = this.genAI.getGenerativeModel({ model });
      
      let prompt;
      if (type === 'image') {
        prompt = 'Analyze this image and provide detailed insights about its content, style, and potential use cases.';
      } else if (type === 'video') {
        prompt = 'Analyze this video and provide insights about its content, style, and key moments.';
      } else {
        prompt = 'Analyze the following content and provide insights about its structure, tone, and effectiveness.';
      }

      const result = await genModel.generateContent([prompt, content]);
      const response = await result.response;

      return {
        analysis: response.text(),
        model,
        provider: 'google'
      };
    } catch (error) {
      logger.error('Google content analysis failed:', error);
      throw error;
    }
  }

  async getQuote(model) {
    // Google Gemini does not have a public pricing API, so we use the configured value
    return (this.costPerToken || 0) * 1000000;
  }
}