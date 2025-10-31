import { ProviderFactory } from './ProviderFactory.js';
import { PROVIDERS } from '../config/providers.js';
import { logger } from '../utils/logger.js';
import { v4 as uuidv4 } from 'uuid';
import { maxCostPer1M } from '../utils/priceLock.js';

async function getProviderQuote(provider) {
  const aiProvider = ProviderFactory.getProvider(provider);
  return aiProvider.getQuote();
}

export class ContentGenerator {
  constructor() {
    this.cache = new Map();
  }

  async generateContent(request, options = {}) {
    const {
      topic,
      audience,
      tone,
      language = 'en',
      mediaType = 'text',
      provider = 'google',
      keywords = [],
      cta = null,
      aspectRatio = '16:9',
      length = 'medium'
    } = request;

    const requestId = uuidv4();
    logger.info(`Starting content generation: ${requestId}`, { topic, mediaType, provider });

    try {
      const ceiling = maxCostPer1M(provider);
      const actual = await getProviderQuote(provider); // quick /models call
      if (actual > ceiling) {
        throw new Error(`Price lock violated: ${provider} quoted ${actual} > ${ceiling}`);
      }
      const aiProvider = ProviderFactory.getProvider(provider);
      
      // Generate research and insights
      const research = await this.generateResearch(topic, audience, provider);
      
      // Generate content based on media type
      let content;
      switch (mediaType) {
        case 'text':
          content = await this.generateTextContent(topic, audience, tone, research, aiProvider, options);
          break;
        case 'image':
          content = await this.generateImageContent(topic, audience, tone, research, aiProvider, options);
          break;
        case 'video':
          content = await this.generateVideoContent(topic, audience, tone, research, aiProvider, options);
          break;
        case 'audio':
          content = await this.generateAudioContent(topic, audience, tone, research, aiProvider, options);
          break;
        case 'multimodal':
          content = await this.generateMultimodalContent(topic, audience, tone, research, aiProvider, options);
          break;
        default:
          throw new Error(`Unsupported media type: ${mediaType}`);
      }

      // Generate SEO and social media content
      const seoData = await this.generateSEOData(topic, content, aiProvider);
      const socialPosts = await this.generateSocialPosts(topic, content, aiProvider);

      const result = {
        id: requestId,
        content,
        research,
        seo: seoData,
        social: socialPosts,
        metadata: {
          topic,
          audience,
          tone,
          language,
          mediaType,
          provider,
          generatedAt: new Date().toISOString(),
          cost: content.cost || 0,
          usage: content.usage || {}
        }
      };

      logger.info(`Content generation completed: ${requestId}`);
      return result;
    } catch (error) {
      logger.error(`Content generation failed: ${requestId}`, error);
      throw error;
    }
  }

  async generateResearch(topic, audience, provider) {
    try {
      const aiProvider = ProviderFactory.getProvider(provider);
      
      const researchPrompt = `Research the topic "${topic}" for audience "${audience}". 
      Provide:
      1. Key insights and trends
      2. Relevant statistics and data
      3. Popular keywords and phrases
      4. Competitor analysis
      5. Content gaps and opportunities
      
      Format as structured JSON.`;

      const research = await aiProvider.generateText(researchPrompt, {
        maxTokens: 2000,
        temperature: 0.3
      });

      // If using Google provider, enhance with web search
      if (provider === PROVIDERS.GOOGLE) {
        try {
          const webResults = await aiProvider.searchWeb(topic, { numResults: 5 });
          research.webResults = webResults.results;
        } catch (error) {
          logger.warn('Web search failed, continuing without web data:', error);
        }
      }

      return research;
    } catch (error) {
      logger.error('Research generation failed:', error);
      return { error: 'Research generation failed', content: '' };
    }
  }

  async generateTextContent(topic, audience, tone, research, aiProvider, options) {
    const { length = 'medium', format = 'article' } = options;
    
    const lengthMap = {
      short: 500,
      medium: 1500,
      long: 3000
    };

    const prompt = `Write a ${format} about "${topic}" for ${audience} audience in a ${tone} tone.
    
    Research insights: ${research.content}
    
    Requirements:
    - Length: ${lengthMap[length]} words
    - Format: ${format}
    - Include engaging headlines and subheadings
    - Add relevant examples and case studies
    - Include a strong call-to-action
    - Optimize for readability and engagement
    
    Structure:
    1. Compelling headline
    2. Introduction with hook
    3. Main content with subheadings
    4. Conclusion with CTA
    5. Key takeaways`;

    const result = await aiProvider.generateText(prompt, {
      maxTokens: lengthMap[length] * 2,
      temperature: 0.7
    });

    return {
      ...result,
      type: 'text',
      format,
      length: lengthMap[length]
    };
  }

  async generateImageContent(topic, audience, tone, research, aiProvider, options) {
    const { aspectRatio = '16:9', style = 'photographic' } = options;
    
    const prompt = `Create an image about "${topic}" for ${audience} audience in a ${tone} style.
    
    Research insights: ${research.content}
    
    Style: ${style}
    Aspect ratio: ${aspectRatio}
    Make it visually appealing and relevant to the topic.`;

    const result = await aiProvider.generateImage(prompt, {
      aspectRatio,
      style
    });

    return {
      ...result,
      type: 'image',
      aspectRatio,
      style
    };
  }

  async generateVideoContent(topic, audience, tone, research, aiProvider, options) {
    const { duration = 30, aspectRatio = '16:9' } = options;
    
    const prompt = `Create a video about "${topic}" for ${audience} audience in a ${tone} tone.
    
    Research insights: ${research.content}
    
    Duration: ${duration} seconds
    Aspect ratio: ${aspectRatio}
    Make it engaging and informative.`;

    const result = await aiProvider.generateVideo(prompt, {
      duration,
      aspectRatio
    });

    return {
      ...result,
      type: 'video',
      duration,
      aspectRatio
    };
  }

  async generateAudioContent(topic, audience, tone, research, aiProvider, options) {
    const { voice = 'alloy', language = 'en-US' } = options;
    
    const prompt = `Create audio content about "${topic}" for ${audience} audience in a ${tone} tone.
    
    Research insights: ${research.content}
    
    Make it engaging and informative for audio consumption.`;

    const result = await aiProvider.generateAudio(prompt, {
      voice,
      language
    });

    return {
      ...result,
      type: 'audio',
      voice,
      language
    };
  }

  async generateMultimodalContent(topic, audience, tone, research, aiProvider, options) {
    // Generate multiple content types and combine them
    const textContent = await this.generateTextContent(topic, audience, tone, research, aiProvider, options);
    const imageContent = await this.generateImageContent(topic, audience, tone, research, aiProvider, options);
    
    // If using Z.AI with tool capabilities, create an integrated workflow
    if (aiProvider.constructor.name === 'ZAIProvider') {
      const tools = [
        {
          type: 'function',
          function: {
            name: 'create_social_post',
            description: 'Create a social media post',
            parameters: {
              type: 'object',
              properties: {
                platform: { type: 'string', enum: ['twitter', 'linkedin', 'instagram'] },
                content: { type: 'string' }
              }
            }
          }
        }
      ];

      const workflowResult = await aiProvider.generateWithTools(
        `Create a comprehensive content strategy for "${topic}" including social media posts for different platforms.`,
        tools
      );

      return {
        type: 'multimodal',
        text: textContent,
        image: imageContent,
        social: workflowResult,
        combined: true
      };
    }

    return {
      type: 'multimodal',
      text: textContent,
      image: imageContent,
      combined: true
    };
  }

  async generateSEOData(topic, content, aiProvider) {
    try {
      const prompt = `Generate SEO metadata for content about "${topic}":
      
      Content: ${content.content || content.images?.[0]?.prompt || 'N/A'}
      
      Provide:
      1. Title tag (50-60 characters)
      2. Meta description (150-160 characters)
      3. Focus keywords (5-10)
      4. H1, H2, H3 structure
      5. Internal linking suggestions
      
      Format as JSON.`;

      const result = await aiProvider.generateText(prompt, {
        maxTokens: 1000,
        temperature: 0.3
      });

      return {
        title: result.content.match(/title[^:]*:([^,}]+)/i)?.[1]?.trim() || topic,
        description: result.content.match(/description[^:]*:([^,}]+)/i)?.[1]?.trim() || '',
        keywords: result.content.match(/keywords[^:]*:([^,}]+)/i)?.[1]?.split(',').map(k => k.trim()) || [],
        structure: result.content
      };
    } catch (error) {
      logger.error('SEO generation failed:', error);
      return {
        title: topic,
        description: `Learn about ${topic}`,
        keywords: [topic],
        structure: ''
      };
    }
  }

  async generateSocialPosts(topic, content, aiProvider) {
    try {
      const platforms = ['twitter', 'linkedin', 'instagram', 'facebook'];
      const posts = {};

      for (const platform of platforms) {
        const prompt = `Create a ${platform} post about "${topic}":
        
        Content: ${content.content || content.images?.[0]?.prompt || 'N/A'}
        
        Platform: ${platform}
        Include relevant hashtags and emojis.
        Keep it engaging and platform-appropriate.`;

        const result = await aiProvider.generateText(prompt, {
          maxTokens: 500,
          temperature: 0.8
        });

        posts[platform] = {
          content: result.content,
          hashtags: result.content.match(/#\w+/g) || [],
          platform
        };
      }

      return posts;
    } catch (error) {
      logger.error('Social posts generation failed:', error);
      return {
        twitter: { content: `Check out this amazing content about ${topic}!`, hashtags: [`#${topic.replace(/\s+/g, '')}`] },
        linkedin: { content: `Professional insights on ${topic}`, hashtags: [`#${topic.replace(/\s+/g, '')}`] }
      };
    }
  }
}
