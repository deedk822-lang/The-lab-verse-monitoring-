const { glm } = require('zai-js');
const OpenAI = require('openai');

class GLMIntegration {
  constructor() {
    this.apiKey = process.env.ZAI_API_KEY;
    if (!this.apiKey) {
      throw new Error('ZAI_API_KEY is required for GLM integration');
    }

    this.client = new OpenAI({
      apiKey: this.apiKey,
      baseURL: "https://open.bigmodel.cn/api/push/v1"
    });
  }

  /**
   * Generate text using GLM-4.7 model
   */
  async generateText(prompt, options = {}) {
    try {
      const response = await this.client.chat.completions.create({
        model: "glm-4-0520", // Latest GLM-4.7 model
        messages: [{ role: "user", content: prompt }],
        temperature: options.temperature || 0.7,
        max_tokens: options.maxTokens || 1024,
        stream: false
      });

      return response.choices[0].message.content;
    } catch (error) {
      console.error('Error generating text with GLM:', error);
      throw error;
    }
  }

  /**
   * Generate structured content using GLM-4.7
   */
  async generateStructuredContent(type, context) {
    const prompt = `
      Generate structured content of type "${type}" based on the following context:
      ${JSON.stringify(context, null, 2)}

      Respond in valid JSON format with the following structure:
      {
        "title": "...",
        "content": "...",
        "tags": [...],
        "metadata": {...}
      }
    `;

    const response = await this.generateText(prompt, { maxTokens: 2048 });

    try {
      return JSON.parse(response);
    } catch (error) {
      console.warn('Failed to parse GLM response as JSON, returning raw text');
      return { content: response };
    }
  }

  /**
   * Analyze content for security issues using GLM-4.7
   */
  async analyzeContentSecurity(content) {
    const prompt = `
      Analyze the following content for potential security issues:
      ${content}

      Identify:
      1. Potential security vulnerabilities
      2. Compliance issues
      3. Risk factors
      4. Recommendations for improvement

      Return your analysis in JSON format:
      {
        "vulnerabilities": [...],
        "complianceIssues": [...],
        "riskFactors": [...],
        "recommendations": [...],
        "overallRiskScore": 0-10
      }
    `;

    const response = await this.generateText(prompt, { maxTokens: 2048 });

    try {
      return JSON.parse(response);
    } catch (error) {
      console.warn('Failed to parse security analysis as JSON');
      return { analysis: response };
    }
  }
}

module.exports = GLMIntegration;
