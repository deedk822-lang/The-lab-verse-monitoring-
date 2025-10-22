import { BaseProvider } from './BaseProvider.js';
import OpenAI from 'openai';
import { logger } from '../../utils/logger.js';

export class OpenAIProvider extends BaseProvider {
  constructor(config) {
    super(config);
    this.openai = new OpenAI({
      apiKey: this.apiKey,
      baseURL: this.baseUrl
    });
  }

  async generateText(prompt, options = {}) {
    const {
      model = 'gpt-4',
      maxTokens = 4000,
      temperature = 0.7,
      stream = false
    } = options;

    this.validateModel(model, 'text');

    try {
      const response = await this.openai.chat.completions.create({
        model,
        messages: [{ role: 'user', content: prompt }],
        max_tokens: Math.min(maxTokens, this.maxTokens),
        temperature,
        stream
      });

      const content = response.choices[0].message.content;
      const usage = response.usage;
      const cost = this.calculateCost(usage.total_tokens);

      return {
        content,
        usage,
        cost,
        model,
        provider: 'openai'
      };
    } catch (error) {
      logger.error('OpenAI text generation failed:', error);
      throw error;
    }
  }

  async generateImage(prompt, options = {}) {
    const {
      model = 'dall-e-3',
      size = '1024x1024',
      quality = 'standard',
      n = 1
    } = options;

    this.validateModel(model, 'image');

    try {
      const response = await this.openai.images.generate({
        model,
        prompt,
        size,
        quality,
        n
      });

      const images = response.data.map(img => ({
        url: img.url,
        revised_prompt: img.revised_prompt
      }));

      return {
        images,
        model,
        provider: 'openai'
      };
    } catch (error) {
      logger.error('OpenAI image generation failed:', error);
      throw error;
    }
  }

  async generateAudio(prompt, options = {}) {
    const {
      model = 'tts-1',
      voice = 'alloy',
      response_format = 'mp3'
    } = options;

    this.validateModel(model, 'audio');

    try {
      const response = await this.openai.audio.speech.create({
        model,
        input: prompt,
        voice,
        response_format
      });

      const audioBuffer = Buffer.from(await response.arrayBuffer());
      const base64Audio = audioBuffer.toString('base64');

      return {
        audio: base64Audio,
        format: response_format,
        model,
        provider: 'openai'
      };
    } catch (error) {
      logger.error('OpenAI audio generation failed:', error);
      throw error;
    }
  }

  async analyzeContent(content, options = {}) {
    const {
      model = 'gpt-4-vision-preview',
      type = 'text'
    } = options;

    try {
      let messages;
      
      if (type === 'image' && typeof content === 'string') {
        messages = [{
          role: 'user',
          content: [
            { type: 'text', text: 'Analyze this image and provide a detailed description.' },
            { type: 'image_url', image_url: { url: content } }
          ]
        }];
      } else {
        messages = [{
          role: 'user',
          content: `Analyze the following ${type} content and provide insights: ${content}`
        }];
      }

      const response = await this.openai.chat.completions.create({
        model,
        messages,
        max_tokens: 1000
      });

      return {
        analysis: response.choices[0].message.content,
        model,
        provider: 'openai'
      };
    } catch (error) {
      logger.error('OpenAI content analysis failed:', error);
      throw error;
    }
  }
}