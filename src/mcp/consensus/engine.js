import { logger } from '../../monitoring/logger.js';

export class ConsensusEngine {
  constructor() {
    this.votingStrategies = {
      'majority': this.majorityVote.bind(this),
      'weighted': this.weightedVote.bind(this),
      'unanimous': this.unanimousVote.bind(this)
    };
  }
  
  /**
   * Analyze consensus from multiple model results
   */
  async analyze(options) {
    const {
      results,
      threshold = 0.66,
      strategy = 'majority'
    } = options;
    
    // Filter successful results
    const successful = results
      .filter(r => r.status === 'fulfilled')
      .map(r => r.value);
    
    if (successful.length === 0) {
      throw new Error('All models failed');
    }
    
    // Extract answers
    const votes = successful.map(result => ({
      model: result.provider,
      answer: this.extractAnswer(result.text),
      confidence: result.confidence || 0.8,
      reasoning: result.text
    }));
    
    // Apply voting strategy
    const votingFn = this.votingStrategies[strategy];
    const consensus = votingFn(votes, threshold);
    
    logger.info(`🗳️ Consensus: ${consensus.decision} (${(consensus.confidence * 100).toFixed(1)}% confidence)`);
    
    return {
      decision: consensus.decision,
      confidence: consensus.confidence,
      votes,
      agreement: consensus.agreement,
      strategy,
      totalModels: results.length,
      successfulModels: successful.length
    };
  }
  
  /**
   * Majority vote - most common answer wins
   */
  majorityVote(votes, threshold) {
    const counts = {};
    
    votes.forEach(vote => {
      counts[vote.answer] = (counts[vote.answer] || 0) + 1;
    });
    
    const sorted = Object.entries(counts).sort((a, b) => b[1] - a[1]);
    const winner = sorted[0];
    const agreement = winner[1] / votes.length;
    
    if (agreement < threshold) {
      return {
        decision: null,
        confidence: agreement,
        agreement,
        reason: 'No consensus reached'
      };
    }
    
    return {
      decision: winner[0],
      confidence: agreement,
      agreement
    };
  }
  
  /**
   * Weighted vote - considers model confidence
   */
  weightedVote(votes, threshold) {
    const weights = {};
    const totalWeight = {};
    
    votes.forEach(vote => {
      if (!weights[vote.answer]) {
        weights[vote.answer] = 0;
        totalWeight[vote.answer] = 0;
      }
      weights[vote.answer] += vote.confidence;
      totalWeight[vote.answer] += 1;
    });
    
    // Calculate weighted scores
    const scores = Object.entries(weights).map(([answer, weight]) => ({
      answer,
      score: weight / votes.length,
      count: totalWeight[answer]
    }));
    
    const sorted = scores.sort((a, b) => b.score - a.score);
    const winner = sorted[0];
    
    if (winner.score < threshold) {
      return {
        decision: null,
        confidence: winner.score,
        agreement: winner.count / votes.length,
        reason: 'Weighted consensus not reached'
      };
    }
    
    return {
      decision: winner.answer,
      confidence: winner.score,
      agreement: winner.count / votes.length
    };
  }
  
  /**
   * Unanimous vote - all models must agree
   */
  unanimousVote(votes, threshold) {
    const firstAnswer = votes[0].answer;
    const allAgree = votes.every(v => v.answer === firstAnswer);
    
    if (!allAgree) {
      return {
        decision: null,
        confidence: 0,
        agreement: 0,
        reason: 'Models disagree'
      };
    }
    
    const avgConfidence = votes.reduce((sum, v) => sum + v.confidence, 0) / votes.length;
    
    return {
      decision: firstAnswer,
      confidence: avgConfidence,
      agreement: 1.0
    };
  }
  
  /**
   * Extract answer from model response
   */
  extractAnswer(text) {
    // Try to extract yes/no
    const lowerText = text.toLowerCase();
    
    if (lowerText.includes('yes') && !lowerText.includes('no')) return 'yes';
    if (lowerText.includes('no') && !lowerText.includes('yes')) return 'no';
    
    // Try to extract true/false
    if (lowerText.includes('true') && !lowerText.includes('false')) return 'true';
    if (lowerText.includes('false') && !lowerText.includes('true')) return 'false';
    
    // Return first sentence as answer
    const sentences = text.split(/[.!?]/);
    return sentences[0].trim();
  }
  
  /**
   * Analyze disagreement patterns
   */
  analyzeDisagreement(votes) {
    const patterns = {
      polarized: false,
      nuanced: false,
      uncertain: false
    };
    
    // Check for polarization (clear split)
    const answers = votes.map(v => v.answer);
    const unique = [...new Set(answers)];
    
    if (unique.length === 2) {
      const split = answers.filter(a => a === unique[0]).length / answers.length;
      if (split > 0.4 && split < 0.6) {
        patterns.polarized = true;
      }
    }
    
    // Check for nuanced differences
    if (unique.length > 2) {
      patterns.nuanced = true;
    }
    
    // Check for uncertainty
    const avgConfidence = votes.reduce((sum, v) => sum + v.confidence, 0) / votes.length;
    if (avgConfidence < 0.7) {
      patterns.uncertain = true;
    }
    
    return patterns;
  }
}
