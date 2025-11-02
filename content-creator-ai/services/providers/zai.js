const axios = require('axios');
const config = require('../../config/config');
const logger = require('../../utils/logger');
const costTracker = require('../../utils/cost-tracker');

class ZAIProvider {
  constructor() {
    this.enabled = config.providers.zai.enabled;
    this.endpoint = config.providers.zai.endpoint;
    this.apiKey = config.providers.zai.apiKey;
    this.model = config.providers.zai.model;
  }

  async generateText(prompt, options = {}) {
    if (!this.enabled) {
      throw new Error('Z.AI provider not enabled. Please set ZAI_API_KEY.');
    }

    try {
      const messages = [
        { role: 'system', content: 'You are a helpful AI assistant specialized in content creation and research.' },
        { role: 'user', content: prompt }
      ];

      // GLM-4.6 supports thinking mode for complex reasoning
      const requestBody = {
        model: this.model,
        messages,
        temperature: options.temperature || 0.7,
        max_tokens: options.maxTokens || 4096,
        stream: options.streaming || false
      };

      // Enable thinking mode for complex queries
      if (options.thinkingMode) {
        requestBody.thinking = true;
      }

      const response = await axios.post(this.endpoint, requestBody, {
        headers: {
          'Authorization': `Bearer ${this.apiKey}`,
          'Content-Type': 'application/json'
        },
        timeout: 60000
      });

      const choice = response.data.choices[0];
      const text = choice.message.content;
      const usage = response.data.usage || {};

      // Track costs - GLM-4.6 is cost-efficient
      const cost = costTracker.calculateTokenCost(
        'zai',
        this.model,
        usage.prompt_tokens || 0,
        usage.completion_tokens || 0
      );

      logger.info(`Z.AI GLM-4.6 text generated: ${text.length} chars, cost: $${cost.toFixed(4)}`);

      // If thinking mode was enabled, extract reasoning
      const thinking = choice.message.thinking || null;

      return {
        text,
        thinking, // Contains the model's reasoning process
        usage: {
          inputTokens: usage.prompt_tokens || 0,
          outputTokens: usage.completion_tokens || 0,
          totalTokens: usage.total_tokens || 0
        },
        cost
      };
    } catch (error) {
      logger.error('Z.AI text generation error:', error.response?.data || error.message);
      throw error;
    }
  }

  async generateWithStreaming(prompt, onChunk, options = {}) {
    if (!this.enabled) {
      throw new Error('Z.AI provider not enabled.');
    }

    try {
      const messages = [
        { role: 'system', content: 'You are a helpful AI assistant.' },
        { role: 'user', content: prompt }
      ];

      const response = await axios.post(this.endpoint, {
        model: this.model,
        messages,
        temperature: options.temperature || 0.7,
        max_tokens: options.maxTokens || 4096,
        stream: true
      }, {
        headers: {
          'Authorization': `Bearer ${this.apiKey}`,
          'Content-Type': 'application/json'
        },
        responseType: 'stream',
        timeout: 60000
      });

      let fullText = '';

      return new Promise((resolve, reject) => {
        response.data.on('data', (chunk) => {
          const lines = chunk.toString().split('\n').filter(line => line.trim() !== '');
          
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const data = line.slice(6);
              if (data === '[DONE]') continue;
              
              try {
                const parsed = JSON.parse(data);
                const content = parsed.choices[0]?.delta?.content || '';
                if (content) {
                  fullText += content;
                  onChunk(content);
                }
              } catch (e) {
                // Ignore parse errors for incomplete chunks
              }
            }
          }
        });

        response.data.on('end', () => {
          resolve({ text: fullText });
        });

        response.data.on('error', reject);
      });
    } catch (error) {
      logger.error('Z.AI streaming error:', error);
      throw error;
    }
  }

  async performResearch(query, options = {}) {
    // Use GLM-4.6 with thinking mode for better reasoning
    const researchPrompt = `Research the following topic comprehensively and provide detailed, accurate information:\n\n${query}\n\nProvide:\n1. Overview and context\n2. Key facts and statistics\n3. Recent developments\n4. Important considerations\n\nBe thorough and cite reasoning where applicable.`;
    
    const result = await this.generateText(researchPrompt, {
      ...options,
      thinkingMode: true, // Enable reasoning for research
      maxTokens: 8000
    });
    
    return {
      summary: result.text,
      thinking: result.thinking, // The model's reasoning process
      searchResults: [],
      sources: [],
      usage: result.usage,
      cost: result.cost
    };
  }

  async agenticTask(task, tools = [], options = {}) {
    // GLM-4.6 supports agentic workflows with tool use
    if (!this.enabled) {
      throw new Error('Z.AI provider not enabled.');
    }

    try {
      const response = await axios.post(this.endpoint, {
        model: this.model,
        messages: [
          { role: 'system', content: 'You are an AI agent capable of using tools to complete tasks.' },
          { role: 'user', content: task }
        ],
        tools: tools, // OpenAI-compatible tool definitions
        temperature: options.temperature || 0.7,
        max_tokens: options.maxTokens || 8000
      }, {
        headers: {
          'Authorization': `Bearer ${this.apiKey}`,
          'Content-Type': 'application/json'
        }
      });

      return response.data;
    } catch (error) {
      logger.error('Z.AI agentic task error:', error);
      throw error;
    }
  }

  async longContextTask(prompt, context, options = {}) {
    // GLM-4.6 supports up to 200K tokens context
    if (!this.enabled) {
      throw new Error('Z.AI provider not enabled.');
    }

    const fullPrompt = `Context:\n${context}\n\nTask:\n${prompt}`;

    return this.generateText(fullPrompt, {
      ...options,
      maxTokens: Math.min(options.maxTokens || 8000, config.providers.zai.maxTokens)
    });
  }

  isEnabled() {
    return this.enabled;
  }
}

module.exports = new ZAIProvider();
