const googleProvider = require('./providers/google');
const localaiProvider = require('./providers/localai');
const zaiProvider = require('./providers/zai');
const openaiProvider = require('./providers/openai');
const logger = require('../utils/logger');
const cache = require('../utils/cache');
const config = require('../config/config');
const { marked } = require('marked');

class ContentGenerator {
  constructor() {
    this.providers = {
      google: googleProvider,
      localai: localaiProvider,
      zai: zaiProvider,
      openai: openaiProvider
    };
  }

  selectProvider(preferredProvider) {
    // Auto-select if not specified or 'auto'
    if (!preferredProvider || preferredProvider === 'auto') {
      preferredProvider = config.providers.default;
    }

    const provider = this.providers[preferredProvider];
    
    if (!provider || !provider.isEnabled()) {
      // Fallback to first available provider
      for (const [name, prov] of Object.entries(this.providers)) {
        if (prov.isEnabled()) {
          logger.info(`Provider ${preferredProvider} not available, falling back to ${name}`);
          return prov;
        }
      }
      throw new Error('No AI providers are enabled. Please configure at least one provider.');
    }

    return provider;
  }

  async generateContent(request) {
    const { media_type, provider: preferredProvider } = request;

    try {
      // Check cache first
      const cacheKey = cache.generateCacheKey(preferredProvider, media_type, request);
      const cached = await cache.get(cacheKey);
      if (cached) {
        logger.info('Returning cached content');
        return { ...cached, fromCache: true };
      }

      let result;

      switch (media_type) {
        case 'text':
          result = await this.generateTextContent(request);
          break;
        case 'image':
          result = await this.generateImageContent(request);
          break;
        case 'video':
          result = await this.generateVideoContent(request);
          break;
        case 'audio':
          result = await this.generateAudioContent(request);
          break;
        case 'multimodal':
          result = await this.generateMultimodalContent(request);
          break;
        default:
          throw new Error(`Unsupported media type: ${media_type}`);
      }

      // Cache the result
      await cache.set(cacheKey, result);

      return result;
    } catch (error) {
      logger.error('Content generation error:', error);
      throw error;
    }
  }

  async generateTextContent(request) {
    const { topic, audience, tone, language, length, format, enable_research, provider: preferredProvider, temperature, max_tokens } = request;
    
    const provider = this.selectProvider(preferredProvider);
    let totalCost = 0;
    let research = null;

    // Step 1: Research (if enabled)
    if (enable_research) {
      logger.info(`Performing research on: ${topic}`);
      research = await provider.performResearch(topic, { temperature, max_tokens });
      totalCost += research.cost || 0;
    }

    // Step 2: Generate content
    const contentPrompt = this.buildTextPrompt(topic, audience, tone, language, length, research);
    logger.info('Generating text content...');
    
    const contentResult = await provider.generateText(contentPrompt, {
      temperature: temperature || 0.7,
      maxTokens: this.getLengthTokens(length)
    });
    
    totalCost += contentResult.cost || 0;

    // Step 3: Format the content
    let formattedContent = contentResult.text;
    if (format === 'html') {
      formattedContent = marked(contentResult.text);
    }

    return {
      type: 'text',
      content: formattedContent,
      format,
      research: research?.summary || null,
      sources: research?.sources || [],
      usage: {
        research: research?.usage || {},
        content: contentResult.usage
      },
      totalCost,
      provider: preferredProvider || config.providers.default
    };
  }

  async generateImageContent(request) {
    const { topic, style, aspect_ratio, provider: preferredProvider } = request;
    
    const provider = this.selectProvider(preferredProvider);

    // Build image prompt
    const imagePrompt = `Create a ${style} image for: ${topic}. High quality, professional, visually appealing.`;
    
    logger.info('Generating image...');
    const result = await provider.generateImage(imagePrompt, { aspectRatio: aspect_ratio, style });

    return {
      type: 'image',
      imageUrl: result.imageUrl,
      prompt: imagePrompt,
      aspectRatio: aspect_ratio,
      style,
      totalCost: result.cost || 0,
      provider: preferredProvider || config.providers.default
    };
  }

  async generateVideoContent(request) {
    const { topic, duration, aspect_ratio, provider: preferredProvider } = request;
    
    const provider = this.selectProvider(preferredProvider);

    // Build video prompt
    const videoPrompt = `Create an engaging video about: ${topic}. Professional, high-quality visuals.`;
    
    logger.info('Generating video...');
    
    // Check if provider supports video generation
    if (typeof provider.generateVideo !== 'function') {
      throw new Error(`Provider ${preferredProvider} does not support video generation`);
    }

    const result = await provider.generateVideo(videoPrompt, { duration, aspectRatio: aspect_ratio });

    return {
      type: 'video',
      videoUrl: result.videoUrl,
      prompt: videoPrompt,
      duration,
      aspectRatio: aspect_ratio,
      totalCost: result.cost || 0,
      provider: preferredProvider || config.providers.default
    };
  }

  async generateAudioContent(request) {
    const { topic, voice, provider: preferredProvider, enable_research } = request;
    
    const provider = this.selectProvider(preferredProvider);
    let totalCost = 0;
    let script = topic;

    // Generate a script if research is enabled
    if (enable_research) {
      const scriptPrompt = `Create a clear, engaging audio script about: ${topic}. Make it suitable for text-to-speech.`;
      const scriptResult = await provider.generateText(scriptPrompt);
      script = scriptResult.text;
      totalCost += scriptResult.cost || 0;
    }

    logger.info('Generating audio...');
    
    // Check if provider supports audio generation
    if (typeof provider.generateAudio !== 'function') {
      throw new Error(`Provider ${preferredProvider} does not support audio generation`);
    }

    const result = await provider.generateAudio(script, { voice });
    totalCost += result.cost || 0;

    return {
      type: 'audio',
      audioUrl: result.audioUrl,
      script,
      voice,
      totalCost,
      provider: preferredProvider || config.providers.default
    };
  }

  async generateMultimodalContent(request) {
    const { topic, provider: preferredProvider } = request;
    
    // Generate both text and image content
    logger.info('Generating multimodal content (text + image)...');

    const textRequest = { ...request, media_type: 'text' };
    const imageRequest = { ...request, media_type: 'image' };

    const [textResult, imageResult] = await Promise.all([
      this.generateTextContent(textRequest),
      this.generateImageContent(imageRequest)
    ]);

    return {
      type: 'multimodal',
      text: textResult,
      image: imageResult,
      totalCost: textResult.totalCost + imageResult.totalCost,
      provider: preferredProvider || config.providers.default
    };
  }

  buildTextPrompt(topic, audience, tone, language, length, research) {
    let prompt = `Create ${this.getLengthDescription(length)} content about: ${topic}\n\n`;
    prompt += `Target audience: ${audience}\n`;
    prompt += `Tone: ${tone}\n`;
    prompt += `Language: ${language}\n\n`;
    
    if (research) {
      prompt += `Research context:\n${research.summary}\n\n`;
    }
    
    prompt += `Requirements:\n`;
    prompt += `- Write in a ${tone} tone suitable for ${audience}\n`;
    prompt += `- Use clear, engaging language\n`;
    prompt += `- Include relevant examples and details\n`;
    prompt += `- Structure the content well with headings and paragraphs\n`;
    prompt += `- Make it informative and valuable\n`;
    
    return prompt;
  }

  getLengthDescription(length) {
    const descriptions = {
      short: 'a concise, brief (200-400 words)',
      medium: 'a well-developed (600-1000 words)',
      long: 'a comprehensive, detailed (1500-2500 words)'
    };
    return descriptions[length] || descriptions.medium;
  }

  getLengthTokens(length) {
    const tokens = {
      short: 600,
      medium: 1500,
      long: 3500
    };
    return tokens[length] || tokens.medium;
  }
}

module.exports = new ContentGenerator();
