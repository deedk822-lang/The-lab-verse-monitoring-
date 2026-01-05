const fs = require('fs');

class ConfidenceScorer {
  constructor() {
    this.protected_paths = JSON.parse(fs.readFileSync('rainmaker_orchestrator/protected_paths.json', 'utf8'));
  }
  calculate(blueprint, riskAnalysis) {
    let score = 100;

    // Penalty: Touching "Protected" Infrastructure
    if (blueprint.files.some(f => this.protected_paths.some(p => f.path.includes(p)))) {
      return {
        score: 0,
        grade: this.getGrade(0)
      };
    }

    // Penalty: High Complexity (Cyclomatic Complexity proxy)
    if (blueprint.stats.loc > 500) score -= 15;

    // Penalty: Security Findings (from Semgrep/Logic)
    if (riskAnalysis.issues.low > 0) score -= 5 * riskAnalysis.issues.low;
    if (riskAnalysis.issues.medium > 0) score -= 15 * riskAnalysis.issues.medium;

    // Bonus: Includes Tests
    if (blueprint.files.some(f => f.path.includes('test_') || f.path.includes('.spec.'))) {
      score += 10;
    }

    return {
      score: Math.max(0, Math.min(100, score)), // Clamp 0-100
      grade: this.getGrade(score)
    };
  }

  getGrade(score) {
    if (score >= 90) return 'A (Auto-Merge)';
    if (score >= 70) return 'B (Human Review)';
    return 'C (Reject)';
  }
}
