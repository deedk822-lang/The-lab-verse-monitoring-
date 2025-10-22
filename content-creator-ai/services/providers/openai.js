const OpenAI = require('openai');
const config = require('../../config/config');
const logger = require('../../utils/logger');
const costTracker = require('../../utils/cost-tracker');

class OpenAIProvider {
  constructor() {
    this.enabled = config.providers.openai.enabled;
    if (this.enabled) {
      this.client = new OpenAI({
        apiKey: config.providers.openai.apiKey
      });
    }
  }

  async generateText(prompt, options = {}) {
    if (!this.enabled) {
      throw new Error('OpenAI provider not enabled. Please set OPENAI_API_KEY.');
    }

    try {
      const completion = await this.client.chat.completions.create({
        model: options.model || config.providers.openai.models.text,
        messages: [
          { role: 'system', content: 'You are a helpful AI assistant for content creation.' },
          { role: 'user', content: prompt }
        ],
        temperature: options.temperature || 0.7,
        max_tokens: options.maxTokens || 2048
      });

      const text = completion.choices[0].message.content;
      const usage = completion.usage;

      const cost = costTracker.calculateTokenCost(
        'openai',
        completion.model,
        usage.prompt_tokens,
        usage.completion_tokens
      );

      logger.info(`OpenAI text generated: ${text.length} chars, cost: $${cost.toFixed(4)}`);

      return {
        text,
        usage: {
          inputTokens: usage.prompt_tokens,
          outputTokens: usage.completion_tokens
        },
        cost
      };
    } catch (error) {
      logger.error('OpenAI text generation error:', error);
      throw error;
    }
  }

  async performResearch(query, options = {}) {
    const researchPrompt = `Research the following topic and provide detailed, accurate information:\n\n${query}\n\nProvide a comprehensive summary with key facts, recent developments, and important considerations.`;
    
    const result = await this.generateText(researchPrompt, {
      ...options,
      maxTokens: 3000
    });
    
    return {
      summary: result.text,
      searchResults: [],
      sources: [],
      usage: result.usage,
      cost: result.cost
    };
  }

  async generateImage(prompt, options = {}) {
    if (!this.enabled) {
      throw new Error('OpenAI provider not enabled.');
    }

    try {
      const size = this.convertAspectRatio(options.aspectRatio || '16:9');
      
      const response = await this.client.images.generate({
        model: 'dall-e-3',
        prompt,
        size,
        quality: options.quality || 'standard',
        n: 1
      });

      const imageUrl = response.data[0].url;

      // DALL-E 3 pricing varies by size and quality
      const cost = this.calculateDallE3Cost(size, options.quality);

      logger.info(`OpenAI image generated: ${imageUrl}, cost: $${cost.toFixed(4)}`);

      return {
        imageUrl,
        prompt,
        aspectRatio: options.aspectRatio || '16:9',
        cost
      };
    } catch (error) {
      logger.error('OpenAI image generation error:', error);
      throw error;
    }
  }

  async generateAudio(text, options = {}) {
    if (!this.enabled) {
      throw new Error('OpenAI provider not enabled.');
    }

    try {
      const mp3 = await this.client.audio.speech.create({
        model: config.providers.openai.models.tts,
        voice: options.voice || 'alloy',
        input: text
      });

      const buffer = Buffer.from(await mp3.arrayBuffer());
      const audioUrl = 'data:audio/mp3;base64,' + buffer.toString('base64');

      const cost = costTracker.calculateMediaCost('openai', 'audio', text.length);

      logger.info(`OpenAI audio generated: ${text.length} chars, cost: $${cost.toFixed(4)}`);

      return {
        audioUrl,
        text,
        voice: options.voice || 'alloy',
        cost
      };
    } catch (error) {
      logger.error('OpenAI TTS error:', error);
      throw error;
    }
  }

  async analyzeImage(imageUrl, prompt) {
    if (!this.enabled) {
      throw new Error('OpenAI provider not enabled.');
    }

    try {
      const response = await this.client.chat.completions.create({
        model: config.providers.openai.models.vision,
        messages: [
          {
            role: 'user',
            content: [
              { type: 'text', text: prompt },
              { type: 'image_url', image_url: { url: imageUrl } }
            ]
          }
        ],
        max_tokens: 1000
      });

      const analysis = response.choices[0].message.content;
      const usage = response.usage;

      const cost = costTracker.calculateTokenCost(
        'openai',
        response.model,
        usage.prompt_tokens,
        usage.completion_tokens
      );

      return { analysis, cost };
    } catch (error) {
      logger.error('OpenAI vision error:', error);
      throw error;
    }
  }

  convertAspectRatio(ratio) {
    // DALL-E 3 supports specific sizes
    const ratioMap = {
      '1:1': '1024x1024',
      '16:9': '1792x1024',
      '9:16': '1024x1792'
    };
    return ratioMap[ratio] || '1024x1024';
  }

  calculateDallE3Cost(size, quality) {
    const pricing = {
      '1024x1024': { standard: 0.040, hd: 0.080 },
      '1792x1024': { standard: 0.080, hd: 0.120 },
      '1024x1792': { standard: 0.080, hd: 0.120 }
    };
    return pricing[size]?.[quality || 'standard'] || 0.040;
  }

  isEnabled() {
    return this.enabled;
  }
}

module.exports = new OpenAIProvider();
