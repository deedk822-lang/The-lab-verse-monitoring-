const axios = require('axios');
const config = require('../../config/config');
const logger = require('../../utils/logger');
const costTracker = require('../../utils/cost-tracker');

class LocalAIProvider {
  constructor() {
    this.enabled = config.providers.localai.enabled;
    this.baseUrl = config.providers.localai.url;
  }

  async generateText(prompt, options = {}) {
    if (!this.enabled) {
      throw new Error('LocalAI provider not enabled. Please set LOCALAI_ENABLED=true and configure LOCALAI_URL.');
    }

    try {
      // LocalAI supports OpenAI-compatible API
      const response = await axios.post(`${this.baseUrl}/v1/chat/completions`, {
        model: options.model || config.providers.localai.models.text,
        messages: [
          { role: 'system', content: 'You are a helpful AI assistant for content creation.' },
          { role: 'user', content: prompt }
        ],
        temperature: options.temperature || 0.7,
        max_tokens: options.maxTokens || 2048,
        stream: false
      }, {
        headers: {
          'Content-Type': 'application/json'
        },
        timeout: 60000
      });

      const text = response.data.choices[0].message.content;
      const usage = response.data.usage || {};

      // LocalAI is free (self-hosted)
      const cost = 0;

      logger.info(`LocalAI text generated: ${text.length} chars (free/self-hosted)`);

      return {
        text,
        usage: {
          inputTokens: usage.prompt_tokens || 0,
          outputTokens: usage.completion_tokens || 0
        },
        cost
      };
    } catch (error) {
      logger.error('LocalAI text generation error:', error.message);
      throw new Error(`LocalAI error: ${error.message}. Make sure LocalAI is running at ${this.baseUrl}`);
    }
  }

  async performResearch(query, options = {}) {
    // LocalAI doesn't have built-in search, so we use the LLM's knowledge
    const researchPrompt = `Research and provide detailed information about: ${query}\n\nProvide a comprehensive summary with key facts and important details.`;
    
    const result = await this.generateText(researchPrompt, options);
    
    return {
      summary: result.text,
      searchResults: [],
      sources: [],
      usage: result.usage,
      cost: 0
    };
  }

  async generateImage(prompt, options = {}) {
    if (!this.enabled) {
      throw new Error('LocalAI provider not enabled.');
    }

    try {
      // LocalAI supports Stable Diffusion and other image models
      const response = await axios.post(`${this.baseUrl}/v1/images/generations`, {
        prompt,
        model: options.model || 'stablediffusion',
        size: this.convertAspectRatio(options.aspectRatio || '16:9'),
        n: 1
      }, {
        timeout: 120000 // Image generation can take longer
      });

      const imageUrl = response.data.data[0].url;

      logger.info(`LocalAI image generated: ${imageUrl}`);

      return {
        imageUrl,
        prompt,
        aspectRatio: options.aspectRatio || '16:9',
        cost: 0 // Free/self-hosted
      };
    } catch (error) {
      logger.error('LocalAI image generation error:', error.message);
      throw error;
    }
  }

  async generateAudio(text, options = {}) {
    if (!this.enabled) {
      throw new Error('LocalAI provider not enabled.');
    }

    try {
      // LocalAI supports TTS with models like Piper
      const response = await axios.post(`${this.baseUrl}/tts`, {
        input: text,
        model: config.providers.localai.models.tts || 'piper',
        voice: options.voice || 'default'
      }, {
        responseType: 'arraybuffer',
        timeout: 60000
      });

      // In a real implementation, you'd save this to a file or cloud storage
      const audioBuffer = Buffer.from(response.data);
      const audioUrl = 'data:audio/wav;base64,' + audioBuffer.toString('base64');

      logger.info(`LocalAI audio generated: ${text.length} chars`);

      return {
        audioUrl,
        text,
        voice: options.voice || 'default',
        cost: 0
      };
    } catch (error) {
      logger.error('LocalAI TTS error:', error.message);
      throw error;
    }
  }

  convertAspectRatio(ratio) {
    const ratioMap = {
      '1:1': '512x512',
      '16:9': '768x432',
      '9:16': '432x768',
      '4:3': '640x480',
      '3:4': '480x640'
    };
    return ratioMap[ratio] || '768x432';
  }

  async checkHealth() {
    if (!this.enabled) {
      return { status: 'disabled' };
    }

    try {
      const response = await axios.get(`${this.baseUrl}/readyz`, { timeout: 5000 });
      return { status: 'healthy', data: response.data };
    } catch (error) {
      logger.error('LocalAI health check failed:', error.message);
      return { status: 'unhealthy', error: error.message };
    }
  }

  isEnabled() {
    return this.enabled;
  }
}

module.exports = new LocalAIProvider();
