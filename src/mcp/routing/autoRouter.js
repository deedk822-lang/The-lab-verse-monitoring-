import { logger } from '../../monitoring/logger.js';

export class AutoRouter {
  constructor() {
    // Provider tiers with pricing (per 1K tokens)
    this.pricing = {
      // Premium tier
      'openai': { input: 0.03, output: 0.06, quality: 0.95 },
      'anthropic': { input: 0.015, output: 0.075, quality: 0.95 },
      
      // Balanced tier
      'gemini': { input: 0.00125, output: 0.005, quality: 0.85 },
      'mistral': { input: 0.002, output: 0.006, quality: 0.85 },
      'perplexity': { input: 0.001, output: 0.005, quality: 0.80 },
      
      // Fast tier
      'groq': { input: 0.0005, output: 0.0008, quality: 0.75 },
      
      // Budget tier
      'deepseek': { input: 0.0001, output: 0.0002, quality: 0.70 },
      'moonshot': { input: 0.0002, output: 0.0004, quality: 0.70 },
      'glm': { input: 0.0001, output: 0.0003, quality: 0.65 }
    };
    
    // Fallback chains by tier
    this.fallbackChains = {
      'openai': ['openai', 'anthropic', 'gemini', 'groq'],
      'anthropic': ['anthropic', 'openai', 'gemini', 'groq'],
      'gemini': ['gemini', 'mistral', 'groq', 'deepseek'],
      'groq': ['groq', 'gemini', 'deepseek'],
      'deepseek': ['deepseek', 'moonshot', 'glm']
    };
  }
  
  /**
   * Select optimal provider based on strategy
   */
  async selectProvider(options) {
    const {
      complexity,
      optimize,
      maxCost,
      availableProviders
    } = options;
    
    // Filter available providers
    const candidates = availableProviders.filter(p => this.pricing[p]);
    
    if (candidates.length === 0) {
      throw new Error('No available providers');
    }
    
    // Select based on optimization strategy
    switch (optimize) {
      case 'cost':
        return this.selectByCost(candidates, complexity);
      
      case 'quality':
        return this.selectByQuality(candidates);
      
      case 'speed':
        return this.selectBySpeed(candidates);
      
      case 'balanced':
      default:
        return this.selectBalanced(candidates, complexity, maxCost);
    }
  }
  
  /**
   * Select cheapest provider that meets quality threshold
   */
  selectByCost(candidates, complexity) {
    const minQuality = complexity.complexity === 'complex' ? 0.80 : 0.65;
    
    const sorted = candidates
      .filter(p => this.pricing[p].quality >= minQuality)
      .sort((a, b) => {
        const costA = this.pricing[a].input + this.pricing[a].output;
        const costB = this.pricing[b].input + this.pricing[b].output;
        return costA - costB;
      });
    
    const provider = sorted[0];
    logger.info(`💰 Cost-optimized: ${provider} ($${this.estimateCost(provider, 1000)})`);
    
    return {
      name: provider,
      reason: 'cost-optimized',
      estimatedCost: this.estimateCost(provider, 1000)
    };
  }
  
  /**
   * Select highest quality provider
   */
  selectByQuality(candidates) {
    const sorted = candidates.sort((a, b) => 
      this.pricing[b].quality - this.pricing[a].quality
    );
    
    const provider = sorted[0];
    logger.info(`🏆 Quality-optimized: ${provider} (score: ${this.pricing[provider].quality})`);
    
    return {
      name: provider,
      reason: 'quality-optimized',
      quality: this.pricing[provider].quality
    };
  }
  
  /**
   * Select fastest provider
   */
  selectBySpeed(candidates) {
    // Fast tier providers
    const fastProviders = ['groq', 'gemini', 'deepseek'];
    const fastest = candidates.find(p => fastProviders.includes(p)) || candidates[0];
    
    logger.info(`⚡ Speed-optimized: ${fastest}`);
    
    return {
      name: fastest,
      reason: 'speed-optimized'
    };
  }
  
  /**
   * Balanced selection based on complexity and cost
   */
  selectBalanced(candidates, complexity, maxCost) {
    const scores = candidates.map(provider => {
      const pricing = this.pricing[provider];
      const cost = this.estimateCost(provider, 1000);
      
      // Score formula: quality / (cost * complexity_multiplier)
      const complexityMultiplier = {
        'simple': 0.5,
        'moderate': 1.0,
        'complex': 2.0
      }[complexity.complexity];
      
      const score = pricing.quality / (cost * complexityMultiplier);
      
      return { provider, score, cost };
    });
    
    // Filter by max cost if specified
    const filtered = maxCost 
      ? scores.filter(s => s.cost <= maxCost)
      : scores;
    
    if (filtered.length === 0) {
      throw new Error(`No providers within budget: $${maxCost}`);
    }
    
    // Select highest score
    const best = filtered.sort((a, b) => b.score - a.score)[0];
    
    logger.info(`⚖️ Balanced: ${best.provider} (score: ${best.score.toFixed(2)})`);
    
    return {
      name: best.provider,
      reason: 'balanced',
      score: best.score,
      estimatedCost: best.cost
    };
  }
  
  /**
   * Get fallback chain for provider
   */
  getFallbackChain(providerName) {
    return this.fallbackChains[providerName] || [providerName];
  }
  
  /**
   * Estimate cost for tokens
   */
  estimateCost(provider, tokens) {
    const pricing = this.pricing[provider];
    if (!pricing) return 0;
    
    // Assume 50/50 input/output split
    const inputCost = (tokens / 2 / 1000) * pricing.input;
    const outputCost = (tokens / 2 / 1000) * pricing.output;
    
    return inputCost + outputCost;
  }
}
