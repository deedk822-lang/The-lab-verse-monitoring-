const fs = require('fs');
const micromatch = require('micromatch');
const { SecureLogger } = require('../utils/SecureLogger');

const logger = new SecureLogger();

class ConfidenceScorer {
  constructor() {
    this.protected_paths = JSON.parse(fs.readFileSync('.jules/protected_paths.json', 'utf8')).protected_paths;
  }
  calculate(blueprint, riskAnalysis) {
    logger.info('Calculating confidence score', {
        filesChanged: blueprint.files?.length || 0
    });

    let score = 100;
    const penalties = [];

    // Penalty: Touching "Protected" Infrastructure
    const protectedFilesViolated = blueprint.files.filter(f => micromatch.isMatch(f.path, this.protected_paths));
    if (protectedFilesViolated.length > 0) {
        const penalty = protectedFilesViolated.length * 20;
        score -= penalty;
        penalties.push({
            type: 'protected_paths',
            count: protectedFilesViolated.length,
            penalty
        });
        return {
            score: 0,
            blocked: true,
            reason: 'protected_paths_violation',
            files: protectedFilesViolated
        };
    }

    // Penalty: High Complexity (Cyclomatic Complexity proxy)
    if (blueprint.stats.loc > 500) {
        score -= 15;
        penalties.push({ type: 'high_complexity', penalty: 15 });
    }

    // Penalty: Security Findings (from Semgrep/Logic)
    if (riskAnalysis.issues.low > 0) {
        const penalty = 5 * riskAnalysis.issues.low;
        score -= penalty;
        penalties.push({ type: 'security_low', count: riskAnalysis.issues.low, penalty });
    }
    if (riskAnalysis.issues.medium > 0) {
        const penalty = 15 * riskAnalysis.issues.medium;
        score -= penalty;
        penalties.push({ type: 'security_medium', count: riskAnalysis.issues.medium, penalty });
    }

    // Bonus: Includes Tests
    if (blueprint.files.some(f => f.path.includes('test_') || f.path.includes('.spec.'))) {
      score += 10;
    }

    const finalScore = Math.max(0, Math.min(100, score));

    logger.info('Confidence score calculated', {
        finalScore: finalScore,
        penalties,
        decision: this.getGrade(finalScore)
    });

    return {
      score: finalScore,
      grade: this.getGrade(finalScore)
    };
  }

  getGrade(score) {
    if (score >= 90) return 'A (Auto-Merge)';
    if (score >= 70) return 'B (Human Review)';
    return 'C (Reject)';
  }
}
