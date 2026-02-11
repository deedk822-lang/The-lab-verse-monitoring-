import { MCPGateway } from './gateway/server.js';
import { AutoRouter } from './routing/autoRouter.js';
import { CostOptimizer } from './optimization/costOptimizer.js';
import { ConsensusEngine } from './consensus/engine.js';
import { MultiModalFusion } from './multimodal/fusion.js';
import { logger } from '../monitoring/logger.js';

export class AIConductor {
  constructor() {
    this.gateway = new MCPGateway();
    this.router = new AutoRouter();
    this.costOptimizer = new CostOptimizer();
    this.consensus = new ConsensusEngine();
    this.multiModal = new MultiModalFusion();

    this.providers = new Map();
    this.loadProviders();
  }

  loadProviders() {
    // AI Providers
    const aiProviders = [
      { name: 'openai', key: process.env.OPENAI_API_KEY, tier: 'premium' },
      { name: 'anthropic', key: process.env.ANTHROPIC_API_KEY, tier: 'premium' },
      { name: 'groq', key: process.env.GROQ_API_KEY, tier: 'fast' },
      { name: 'gemini', key: process.env.GEMINI_API_KEY, tier: 'balanced' },
      { name: 'deepseek', key: process.env.DEEPSEEK_V3_1_API_KEY, tier: 'budget' },
      { name: 'mistral', key: process.env.MISTRALAI_API_KEY, tier: 'balanced' },
      { name: 'perplexity', key: process.env.PERPLEXITY_API_KEY, tier: 'research' },
      { name: 'moonshot', key: process.env.MOONSHOT_API_KEY, tier: 'budget' },
      { name: 'glm', key: process.env.GLM_4_6_API_KEY, tier: 'budget' },
      { name: 'qwen', key: process.env.QWEN3_VL_8B_API_KEY, tier: 'vision' },
      { name: 'tongyi', key: process.env.TONGYI_API_KEY, tier: 'chinese' },
      { name: 'dashscope', key: process.env.DASHSCOPE_API_KEY, tier: 'chinese' },
    ];

    // Integration Providers
    const integrations = [
      { name: 'elevenlabs', key: process.env.ELEVENLAPS_API_KEY, type: 'audio' },
      { name: 'whatsapp', key: process.env.WHATSAPP_PHONE_ID, type: 'messaging' },
      { name: 'slack', key: process.env.SLACK_WEBHOOK_URL, type: 'messaging' },
      { name: 'asana', key: process.env.ASANA_INTEGRATIONS_ACTIONS, type: 'productivity' },
      { name: 'aryshare', key: process.env.ARYSHARE_API_KEY, type: 'social' },
      { name: 'newsai', key: process.env.NEWSAI_API_KEY, type: 'content' },
    ];

    // Load AI providers
    aiProviders.forEach(provider => {
      if (provider.key) {
        this.providers.set(provider.name, {
          ...provider,
          status: 'active',
          lastCheck: Date.now(),
        });
        logger.info(`✅ Loaded AI provider: ${provider.name} (${provider.tier})`);
      }
    });

    // Load integrations
    integrations.forEach(integration => {
      if (integration.key) {
        this.providers.set(integration.name, {
          ...integration,
          status: 'active',
          lastCheck: Date.now(),
        });
        logger.info(`✅ Loaded integration: ${integration.name} (${integration.type})`);
      }
    });

    logger.info(`🎯 Total providers loaded: ${this.providers.size}`);
  }

  /**
   * Smart Generate - Auto-routes based on optimization strategy
   */
  async generate(options) {
    const {
      prompt,
      optimize = 'balanced', // 'cost', 'quality', 'speed', 'balanced'
      maxCost = null,
      fallback = true,
    } = options;

    try {
      // 1. Analyze prompt complexity
      const complexity = await this.analyzeComplexity(prompt);

      // 2. Get optimal provider
      const provider = await this.router.selectProvider({
        complexity,
        optimize,
        maxCost,
        availableProviders: Array.from(this.providers.keys()),
      });

      logger.info(`🎯 Routing to: ${provider.name} (${optimize} mode)`);

      // 3. Execute with fallback
      const result = await this.executeWithFallback(provider, prompt, fallback);

      // 4. Track costs
      await this.costOptimizer.track({
        provider: provider.name,
        cost: result.cost,
        tokens: result.usage,
      });

      return result;

    } catch (error) {
      logger.error('Generate failed:', error);
      throw error;
    }
  }

  /**
   * Consensus Voting - Query multiple models
   */
  async consensus(options) {
    const {
      prompt,
      models = ['gpt-4', 'claude-3', 'gemini-pro'],
      threshold = 0.66,
    } = options;

    try {
      // Execute in parallel
      const results = await Promise.allSettled(
        models.map(model => this.executeSingle(model, prompt)),
      );

      // Analyze consensus
      const consensusResult = await this.consensus.analyze({
        results,
        threshold,
      });

      logger.info(`🗳️ Consensus: ${consensusResult.decision} (${consensusResult.confidence})`);

      return consensusResult;

    } catch (error) {
      logger.error('Consensus failed:', error);
      throw error;
    }
  }

  /**
   * Multi-Modal Fusion - Combine text, image, audio, video
   */
  async multiModal(options) {
    const {
      text,
      image,
      audio,
      providers = {},
    } = options;

    try {
      const tasks = [];

      // Vision task
      if (image) {
        tasks.push(this.multiModal.processVision({
          image,
          provider: providers.vision || 'gemini-pro-vision',
        }));
      }

      // Audio task
      if (audio || providers.audio) {
        tasks.push(this.multiModal.processAudio({
          text,
          provider: providers.audio || 'elevenlabs',
        }));
      }

      // Text task
      if (text) {
        tasks.push(this.multiModal.processText({
          text,
          provider: providers.text || 'gpt-4',
        }));
      }

      // Execute all tasks
      const results = await Promise.all(tasks);

      // Fuse results
      const fused = await this.multiModal.fuse(results);

      return fused;

    } catch (error) {
      logger.error('Multi-modal fusion failed:', error);
      throw error;
    }
  }

  /**
   * A/B Testing Engine
   */
  async abTest(options) {
    const {
      variants,
      metric,
      sampleSize = 100,
    } = options;

    try {
      const results = [];

      for (const variant of variants) {
        const samples = await this.runSamples(variant, sampleSize);
        results.push({
          variant,
          samples,
          score: this.calculateScore(samples, metric),
        });
      }

      // Find winner
      const winner = results.reduce((best, current) =>
        current.score > best.score ? current : best,
      );

      logger.info(`🏆 A/B Test winner: ${winner.variant.model}`);

      return {
        winner,
        results,
        improvement: this.calculateImprovement(results),
      };

    } catch (error) {
      logger.error('A/B test failed:', error);
      throw error;
    }
  }

  /**
   * Cost-Aware Batch Processing
   */
  async batch(options) {
    const {
      prompts,
      optimize = 'cost',
    } = options;

    const maxCost = options.maxCost || null;

    try {
      let totalCost = 0;
      const results = [];

      for (const prompt of prompts) {
        // Check budget
        if (maxCost && totalCost >= maxCost) {
          logger.warn(`💰 Budget limit reached: $${maxCost}`);
          break;
        }

        // Execute with cost tracking
        const result = await this.generate({
          prompt,
          optimize,
          maxCost: maxCost ? maxCost - totalCost : null,
        });

        totalCost += result.cost;
        results.push(result);
      }

      return {
        results,
        totalCost,
        processed: results.length,
        skipped: prompts.length - results.length,
      };

    } catch (error) {
      logger.error('Batch processing failed:', error);
      throw error;
    }
  }

  /**
   * Execute with automatic fallback
   */
  async executeWithFallback(provider, prompt, enableFallback) {
    const fallbackChain = this.router.getFallbackChain(provider.name);

    for (const providerName of fallbackChain) {
      try {
        const result = await this.executeSingle(providerName, prompt);
        return result;
      } catch (error) {
        logger.warn(`❌ ${providerName} failed, trying fallback...`);

        if (!enableFallback || providerName === fallbackChain[fallbackChain.length - 1]) {
          throw error;
        }
      }
    }
  }

  /**
   * Execute single provider call
   */
  async executeSingle(providerName, prompt) {
    const plugin = this.gateway.plugins.get(providerName);
    if (!plugin) {
      throw new Error(`Provider not found: ${providerName}`);
    }

    const startTime = Date.now();
    const result = await plugin.execute('generate', { prompt });
    const duration = Date.now() - startTime;

    return {
      ...result,
      provider: providerName,
      duration,
      cost: this.costOptimizer.calculateCost(providerName, result.usage),
    };
  }

  /**
   * Analyze prompt complexity
   */
  async analyzeComplexity(prompt) {
    const wordCount = prompt.split(/\s+/).length;
    const hasCode = /```/.test(prompt);
    const hasMultiLang = /[\u4e00-\u9fa5]/.test(prompt); // Chinese chars

    let score = 0;
    if (wordCount > 100) score += 2;
    if (wordCount > 500) score += 3;
    if (hasCode) score += 2;
    if (hasMultiLang) score += 1;

    let complexity;
    if (score <= 2) complexity = 'simple';
    else if (score <= 5) complexity = 'moderate';
    else complexity = 'complex';

    return {
      score,
      complexity,
      wordCount,
      hasCode,
      hasMultiLang,
    };
  }

  /**
   * Get system status
   */
  async getStatus() {
    const providerStatus = [];

    for (const [name, provider] of this.providers.entries()) {
      const health = await this.checkProviderHealth(name);
      providerStatus.push({
        name,
        tier: provider.tier || provider.type,
        status: health.status,
        latency: health.latency,
        lastCheck: provider.lastCheck,
      });
    }

    return {
      totalProviders: this.providers.size,
      activeProviders: providerStatus.filter(p => p.status === 'healthy').length,
      providers: providerStatus,
      costs: await this.costOptimizer.getSummary(),
      uptime: process.uptime(),
    };
  }

  /**
   * Check provider health
   */
  async checkProviderHealth(providerName) {
    const startTime = Date.now();

    try {
      const plugin = this.gateway.plugins.get(providerName);
      if (!plugin) {
        return { status: 'unknown', latency: 0 };
      }

      await plugin.healthCheck();
      const latency = Date.now() - startTime;

      return { status: 'healthy', latency };
    } catch (error) {
      return { status: 'unhealthy', latency: 0, error: error.message };
    }
  }
}

// Export singleton
export const conductor = new AIConductor();
