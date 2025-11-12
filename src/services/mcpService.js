import axios from 'axios';
import { logger } from '../utils/logger.js';

class MCPService {
  constructor() {
    // Claude API configuration
    this.claude = {
      apiKey: process.env.CLAUDE_API_KEY,
      baseURL: 'https://api.anthropic.com',
      model: process.env.CLAUDE_MODEL || 'claude-3-5-sonnet-20241022',
      version: '2023-06-01'
    };

    // Mistral API configuration
    this.mistral = {
      apiKey: process.env.MISTRAL_API_KEY,
      baseURL: 'https://api.mistral.ai/v1',
      model: process.env.MISTRAL_MODEL || 'mistral-large-latest'
    };

    // MCP servers configuration
    this.servers = {
      primary: {
        url: process.env.MCP_PRIMARY_URL || 'http://localhost:3001',
        apiKey: process.env.MCP_PRIMARY_API_KEY
      },
      secondary: {
        url: process.env.MCP_SECONDARY_URL,
        apiKey: process.env.MCP_SECONDARY_API_KEY
      }
    };

    this.defaultTimeout = 60000;

    if (!this.claude.apiKey) {
      logger.warn('CLAUDE_API_KEY not found in environment variables');
    }

    if (!this.mistral.apiKey) {
      logger.warn('MISTRAL_API_KEY not found in environment variables');
    }
  }

  /**
   * Generate content using Claude API
   * @param {Object} params - Generation parameters
   * @param {string} params.prompt - Content prompt
   * @param {string} params.systemPrompt - System instructions
   * @param {number} params.maxTokens - Maximum tokens
   * @param {number} params.temperature - Creativity level
   * @returns {Promise<Object>} - Generation result
   */
  async generateWithClaude(params) {
    try {
      if (!this.claude.apiKey) {
        throw new Error('Claude API key not configured');
      }

      const {
        prompt,
        systemPrompt = 'You are a helpful AI assistant that generates high-quality content.',
        maxTokens = 4000,
        temperature = 0.7,
        useComputerUse = false
      } = params;

      const payload = {
        model: this.claude.model,
        max_tokens: maxTokens,
        temperature,
        messages: [
          {
            role: 'user',
            content: prompt
          }
        ]
      };

      // Add system prompt if provided
      if (systemPrompt) {
        payload.system = systemPrompt;
      }

      // Enable computer use capabilities if requested (Claude 3.5 Sonnet)
      if (useComputerUse && this.claude.model.includes('claude-3-5-sonnet')) {
        payload.tools = [
          {
            type: 'computer_20241022',
            name: 'computer',
            display_width_px: 1024,
            display_height_px: 768,
            display_number: 1
          }
        ];
      }

      logger.info('Generating content with Claude:', {
        model: this.claude.model,
        promptLength: prompt.length,
        maxTokens,
        useComputerUse
      });

      const response = await axios.post(
        `${this.claude.baseURL}/v1/messages`,
        payload,
        {
          headers: {
            'x-api-key': this.claude.apiKey,
            'anthropic-version': this.claude.version,
            'content-type': 'application/json'
          },
          timeout: this.defaultTimeout
        }
      );

      const content = response.data.content[0].text;

      logger.info('Claude content generated successfully:', {
        contentLength: content.length,
        model: this.claude.model,
        usage: response.data.usage
      });

      return {
        success: true,
        content,
        metadata: {
          model: this.claude.model,
          usage: response.data.usage,
          provider: 'claude',
          timestamp: new Date().toISOString()
        }
      };

    } catch (error) {
      logger.error('Claude content generation failed:', {
        error: error.message,
        response: error.response?.data
      });

      return {
        success: false,
        error: error.message,
        provider: 'claude'
      };
    }
  }

  /**
   * Generate content using Mistral AI
   * @param {Object} params - Generation parameters
   * @param {string} params.prompt - Content prompt
   * @param {string} params.systemPrompt - System instructions
   * @param {number} params.maxTokens - Maximum tokens
   * @param {number} params.temperature - Creativity level
   * @returns {Promise<Object>} - Generation result
   */
  async generateWithMistral(params) {
    try {
      if (!this.mistral.apiKey) {
        throw new Error('Mistral API key not configured');
      }

      const {
        prompt,
        systemPrompt = 'You are a helpful AI assistant that generates high-quality content.',
        maxTokens = 4000,
        temperature = 0.7,
        stream = false
      } = params;

      const messages = [];

      if (systemPrompt) {
        messages.push({
          role: 'system',
          content: systemPrompt
        });
      }

      messages.push({
        role: 'user',
        content: prompt
      });

      const payload = {
        model: this.mistral.model,
        messages,
        max_tokens: maxTokens,
        temperature,
        stream
      };

      logger.info('Generating content with Mistral:', {
        model: this.mistral.model,
        promptLength: prompt.length,
        maxTokens
      });

      const response = await axios.post(
        `${this.mistral.baseURL}/chat/completions`,
        payload,
        {
          headers: {
            'Authorization': `Bearer ${this.mistral.apiKey}`,
            'Content-Type': 'application/json'
          },
          timeout: this.defaultTimeout
        }
      );

      const content = response.data.choices[0].message.content;

      logger.info('Mistral content generated successfully:', {
        contentLength: content.length,
        model: this.mistral.model,
        usage: response.data.usage
      });

      return {
        success: true,
        content,
        metadata: {
          model: this.mistral.model,
          usage: response.data.usage,
          provider: 'mistral',
          timestamp: new Date().toISOString()
        }
      };

    } catch (error) {
      logger.error('Mistral content generation failed:', {
        error: error.message,
        response: error.response?.data
      });

      return {
        success: false,
        error: error.message,
        provider: 'mistral'
      };
    }
  }

  /**
   * Generate content using the best available provider
   * @param {Object} params - Generation parameters
   * @param {string} params.preferredProvider - Preferred provider (claude, mistral)
   * @param {boolean} params.useFailover - Enable automatic failover
   * @returns {Promise<Object>} - Generation result
   */
  async generateContent(params) {
    try {
      const {
        preferredProvider = 'claude',
        useFailover = true,
        ...otherParams
      } = params;

      let result;

      // Try preferred provider first
      if (preferredProvider === 'claude') {
        result = await this.generateWithClaude(otherParams);

        // Fallback to Mistral if Claude fails and failover is enabled
        if (!result.success && useFailover && this.mistral.apiKey) {
          logger.info('Claude failed, attempting Mistral failover');
          result = await this.generateWithMistral(otherParams);
        }
      } else if (preferredProvider === 'mistral') {
        result = await this.generateWithMistral(otherParams);

        // Fallback to Claude if Mistral fails and failover is enabled
        if (!result.success && useFailover && this.claude.apiKey) {
          logger.info('Mistral failed, attempting Claude failover');
          result = await this.generateWithClaude(otherParams);
        }
      } else {
        throw new Error(`Unknown provider: ${preferredProvider}`);
      }

      return result;

    } catch (error) {
      logger.error('MCP content generation failed:', error.message);
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Generate customer support responses using Claude's expertise
   * @param {Object} params - Support parameters
   * @param {string} params.customerQuery - Customer question/issue
   * @param {Object} params.context - Support context and knowledge base
   * @param {string} params.tone - Response tone (professional, friendly, empathetic)
   * @returns {Promise<Object>} - Support response
   */
  async generateSupportResponse(params) {
    try {
      const {
        customerQuery,
        context = {},
        tone = 'professional',
        includeSteps = true,
        maxTokens = 2000
      } = params;

      let systemPrompt = `You are a helpful customer support agent. Provide clear, accurate, and ${tone} responses to customer inquiries. `;

      if (includeSteps) {
        systemPrompt += 'When appropriate, provide step-by-step instructions. ';
      }

      systemPrompt += 'Always aim to resolve the customer\'s issue completely and offer additional help if needed.';

      let prompt = `Customer Query: ${customerQuery}\n\n`;

      if (context.knowledgeBase) {
        prompt += `Knowledge Base Information:\n${context.knowledgeBase}\n\n`;
      }

      if (context.customerHistory) {
        prompt += `Customer History:\n${context.customerHistory}\n\n`;
      }

      prompt += 'Please provide a helpful response to the customer.';

      const result = await this.generateWithClaude({
        prompt,
        systemPrompt,
        maxTokens,
        temperature: 0.3 // Lower temperature for consistent support responses
      });

      if (result.success) {
        result.metadata.supportType = 'customer_support';
        result.metadata.tone = tone;
      }

      return result;

    } catch (error) {
      logger.error('Support response generation failed:', error.message);
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Analyze financial data using structured prompts
   * @param {Object} params - Analysis parameters
   * @param {Object} params.data - Financial data to analyze
   * @param {string} params.analysisType - Type of analysis
   * @param {Array} params.metrics - Specific metrics to focus on
   * @returns {Promise<Object>} - Financial analysis
   */
  async analyzeFinancialData(params) {
    try {
      const {
        data,
        analysisType = 'comprehensive',
        metrics = [],
        timeframe = 'current',
        includeRecommendations = true
      } = params;

      let systemPrompt = 'You are a financial data analyst. Provide accurate, insightful analysis of financial data. ';
      systemPrompt += 'Focus on trends, patterns, and actionable insights. Present information clearly and professionally.';

      let prompt = 'Financial Data Analysis Request:\n\n';
      prompt += `Analysis Type: ${analysisType}\n`;
      prompt += `Timeframe: ${timeframe}\n\n`;

      if (metrics.length > 0) {
        prompt += `Focus Metrics: ${metrics.join(', ')}\n\n`;
      }

      prompt += `Data:\n${JSON.stringify(data, null, 2)}\n\n`;

      if (includeRecommendations) {
        prompt += 'Please include actionable recommendations based on your analysis.';
      }

      const result = await this.generateWithClaude({
        prompt,
        systemPrompt,
        maxTokens: 3000,
        temperature: 0.2 // Low temperature for factual financial analysis
      });

      if (result.success) {
        result.metadata.analysisType = analysisType;
        result.metadata.metrics = metrics;
        result.metadata.dataPoints = Object.keys(data).length;
      }

      return result;

    } catch (error) {
      logger.error('Financial analysis failed:', error.message);
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Generate multi-lingual content
   * @param {Object} params - Multi-lingual parameters
   * @param {string} params.content - Base content
   * @param {Array} params.targetLanguages - Target languages
   * @param {string} params.tone - Content tone
   * @param {boolean} params.culturalAdaptation - Adapt for cultural context
   * @returns {Promise<Object>} - Multi-lingual content
   */
  async generateMultiLingual(params) {
    try {
      const {
        content,
        targetLanguages = ['es', 'fr', 'de'],
        tone = 'professional',
        culturalAdaptation = true,
        provider = 'mistral' // Mistral excels at multilingual
      } = params;

      const results = {
        original: content,
        translations: {},
        metadata: {
          targetLanguages,
          culturalAdaptation,
          tone
        }
      };

      for (const language of targetLanguages) {
        let prompt = `Translate the following content to ${language}:\n\n${content}\n\n`;
        prompt += `Tone: ${tone}\n`;

        if (culturalAdaptation) {
          prompt += 'Please adapt the content for the target culture and market, not just literal translation.';
        } else {
          prompt += 'Please provide an accurate, literal translation.';
        }

        const translationResult = provider === 'mistral'
          ? await this.generateWithMistral({
            prompt,
            maxTokens: 2000,
            temperature: 0.3
          })
          : await this.generateWithClaude({
            prompt,
            maxTokens: 2000,
            temperature: 0.3
          });

        if (translationResult.success) {
          results.translations[language] = translationResult.content;
        } else {
          results.translations[language] = `Translation failed: ${translationResult.error}`;
        }
      }

      logger.info('Multi-lingual content generation completed:', {
        targetLanguages,
        successful: Object.keys(results.translations).filter(lang =>
          !results.translations[lang].startsWith('Translation failed')
        ).length
      });

      return {
        success: true,
        results,
        provider
      };

    } catch (error) {
      logger.error('Multi-lingual generation failed:', error.message);
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Test connections to all configured services
   * @returns {Promise<Object>} - Connection test results
   */
  async testConnections() {
    try {
      const results = {
        claude: { configured: !!this.claude.apiKey, connected: false },
        mistral: { configured: !!this.mistral.apiKey, connected: false },
        mcpServers: {}
      };

      // Test Claude connection
      if (this.claude.apiKey) {
        const claudeTest = await this.generateWithClaude({
          prompt: 'Hello, this is a connection test.',
          maxTokens: 50,
          temperature: 0.1
        });
        results.claude.connected = claudeTest.success;
        if (!claudeTest.success) {
          results.claude.error = claudeTest.error;
        }
      }

      // Test Mistral connection
      if (this.mistral.apiKey) {
        const mistralTest = await this.generateWithMistral({
          prompt: 'Hello, this is a connection test.',
          maxTokens: 50,
          temperature: 0.1
        });
        results.mistral.connected = mistralTest.success;
        if (!mistralTest.success) {
          results.mistral.error = mistralTest.error;
        }
      }

      // Test MCP servers
      for (const [serverName, server] of Object.entries(this.servers)) {
        if (server.url) {
          try {
            await axios.get(`${server.url}/health`, { timeout: 5000 });
            results.mcpServers[serverName] = { configured: true, connected: true };
          } catch (error) {
            results.mcpServers[serverName] = {
              configured: true,
              connected: false,
              error: error.message
            };
          }
        } else {
          results.mcpServers[serverName] = { configured: false, connected: false };
        }
      }

      logger.info('MCP connection tests completed:', results);

      return {
        success: true,
        results
      };

    } catch (error) {
      logger.error('MCP connection tests failed:', error.message);
      return {
        success: false,
        error: error.message
      };
    }
  }
}

// Export singleton instance
export default new MCPService();
