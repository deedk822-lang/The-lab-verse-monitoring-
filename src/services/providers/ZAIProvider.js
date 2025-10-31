import { BaseProvider } from './BaseProvider.js';
import axios from 'axios';
import { logger } from '../../utils/logger.js';

export class ZAIProvider extends BaseProvider {
  constructor(config) {
    super(config);
    this.features = config.features || {};
  }

  async generateText(prompt, options = {}) {
    const {
      model = 'glm-4.6',
      maxTokens = 4000,
      temperature = 0.7,
      thinkingMode = false,
      stream = false,
      tools = null
    } = options;

    this.validateModel(model, 'text');

    try {
      const requestData = {
        model,
        messages: [{ role: 'user', content: prompt }],
        max_tokens: Math.min(maxTokens, this.maxTokens),
        temperature,
        stream
      };

      // Enable thinking mode for complex reasoning
      if (thinkingMode && this.features.thinkingMode) {
        requestData.thinking = true;
      }

      // Add tools for agentic capabilities
      if (tools && this.features.toolUse) {
        requestData.tools = tools;
      }

      const response = await this.makeRequest('/chat/completions', requestData);

      let content, thinking, toolCalls;
      
      if (stream) {
        // Handle streaming response
        content = await this.handleStreamingResponse(response);
      } else {
        content = response.choices[0].message.content;
        thinking = response.thinking;
        toolCalls = response.choices[0].message.tool_calls;
      }

      const usage = response.usage || { total_tokens: 0 };
      const cost = this.calculateCost(usage.total_tokens);

      return {
        content,
        thinking,
        toolCalls,
        usage,
        cost,
        model,
        provider: 'zai'
      };
    } catch (error) {
      logger.error('Z.AI text generation failed:', error);
      throw error;
    }
  }

  async handleStreamingResponse(response) {
    // Handle streaming response from Z.AI
    let content = '';
    for await (const chunk of response) {
      if (chunk.choices && chunk.choices[0] && chunk.choices[0].delta) {
        const delta = chunk.choices[0].delta;
        if (delta.content) {
          content += delta.content;
        }
      }
    }
    return content;
  }

  async generateWithTools(prompt, tools, options = {}) {
    if (!this.features.toolUse) {
      throw new Error('Tool use not supported by this Z.AI configuration');
    }

    const {
      model = 'glm-4.6',
      maxTokens = 4000,
      temperature = 0.7
    } = options;

    try {
      const response = await this.makeRequest('/chat/completions', {
        model,
        messages: [{ role: 'user', content: prompt }],
        tools,
        tool_choice: 'auto',
        max_tokens: Math.min(maxTokens, this.maxTokens),
        temperature
      });

      const message = response.choices[0].message;
      const usage = response.usage || { total_tokens: 0 };
      const cost = this.calculateCost(usage.total_tokens);

      return {
        content: message.content,
        toolCalls: message.tool_calls,
        usage,
        cost,
        model,
        provider: 'zai'
      };
    } catch (error) {
      logger.error('Z.AI tool generation failed:', error);
      throw error;
    }
  }

  async generateLongContext(prompt, options = {}) {
    if (!this.features.longContext) {
      throw new Error('Long context not supported by this Z.AI configuration');
    }

    const {
      model = 'glm-4.6',
      maxTokens = 200000, // Z.AI supports up to 200K tokens
      temperature = 0.7
    } = options;

    try {
      const response = await this.generateText(prompt, {
        model,
        maxTokens,
        temperature
      });

      return response;
    } catch (error) {
      logger.error('Z.AI long context generation failed:', error);
      throw error;
    }
  }

  async analyzeContent(content, options = {}) {
    const {
      model = 'glm-4.6',
      type = 'text',
      thinkingMode = true
    } = options;

    try {
      let prompt;
      if (type === 'image') {
        prompt = 'Analyze this image and provide detailed insights about its content, composition, and potential use cases.';
      } else if (type === 'video') {
        prompt = 'Analyze this video content and provide insights about its key elements, pacing, and effectiveness.';
      } else {
        prompt = 'Analyze the following content and provide comprehensive insights about its structure, tone, effectiveness, and potential improvements.';
      }

      const response = await this.generateText(`${prompt}\n\nContent: ${content}`, { 
        model, 
        thinkingMode 
      });

      return {
        analysis: response.content,
        thinking: response.thinking,
        model,
        provider: 'zai'
      };
    } catch (error) {
      logger.error('Z.AI content analysis failed:', error);
      throw error;
    }
  }

  async generateCode(prompt, options = {}) {
    const {
      model = 'glm-4.6',
      language = 'javascript',
      framework = null
    } = options;

    try {
      const codePrompt = `Generate ${language} code${framework ? ` using ${framework}` : ''} for the following requirements:\n\n${prompt}\n\nProvide clean, well-commented, production-ready code.`;
      
      const response = await this.generateText(codePrompt, { 
        model,
        thinkingMode: true
      });

      return {
        code: response.content,
        thinking: response.thinking,
        language,
        framework,
        model,
        provider: 'zai'
      };
    } catch (error) {
      logger.error('Z.AI code generation failed:', error);
      throw error;
    }
  }

  async generateAgenticWorkflow(prompt, tools, options = {}) {
    if (!this.features.toolUse) {
      throw new Error('Agentic workflows require tool use capability');
    }

    const {
      model = 'glm-4.6',
      maxIterations = 5
    } = options;

    try {
      let messages = [{ role: 'user', content: prompt }];
      let iteration = 0;
      let finalResult = '';

      while (iteration < maxIterations) {
        const response = await this.generateWithTools(
          messages[messages.length - 1].content,
          tools,
          { model }
        );

        messages.push({
          role: 'assistant',
          content: response.content,
          tool_calls: response.toolCalls
        });

        if (!response.toolCalls || response.toolCalls.length === 0) {
          finalResult = response.content;
          break;
        }

        // Simulate tool execution (in real implementation, execute actual tools)
        const toolResults = response.toolCalls.map(toolCall => ({
          tool_call_id: toolCall.id,
          role: 'tool',
          content: `Tool ${toolCall.function.name} executed successfully`
        }));

        messages.push(...toolResults);
        iteration++;
      }

      return {
        result: finalResult,
        iterations: iteration,
        messages,
        model,
        provider: 'zai'
      };
    } catch (error) {
      logger.error('Z.AI agentic workflow failed:', error);
      throw error;
    }
  }

  async getQuote(model) {
    // Z.AI does not have a public pricing API, so we use the configured value
    return (this.costPerToken || 0) * 1000000;
  }
}