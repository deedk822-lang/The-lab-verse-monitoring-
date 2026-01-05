const { KimiClient } = require('./clients/kimi');
const { FileSystemAgent } = require('./agents/fs');
const { ConfidenceScorer } = require('./governance/scorer');
const { SecurityGate } = require('./governance/security');

class TaskRouter {
  constructor(config) {
    this.kimi = new KimiClient(config.kimi);
    this.fs = new FileSystemAgent(config.fs);
    this.scorer = new ConfidenceScorer();
    this.security = new SecurityGate();
  }

  async handleRequest(intent) {
    console.log(`🧠 [BRAIN] Analyzing intent: "${intent}"`);

    // 1. Context Assembly (RAG-lite)
    const context = await this.fs.getRepoContext({
      includeStructure: true,
      maxTokens: 50000 // Reserve space for generation
    });

    // 2. Kimi Reasoning (The Hybrid Call)
    const blueprint = await this.kimi.generateBlueprint(intent, context);

    // 3. The "SRE" Governance Layer
    const riskAnalysis = await this.security.scanBlueprint(blueprint);
    const confidenceScore = this.scorer.calculate(blueprint, riskAnalysis);

    console.log(`🛡️ [GOVERNANCE] Confidence Score: ${confidenceScore.score}/100`);

    // 4. Decision Matrix
    if (confidenceScore.score >= 90 && !riskAnalysis.hasCritical) {
      return this.autoExecute(blueprint);
    } else if (confidenceScore.score >= 70) {
      return this.createPullRequest(blueprint, riskAnalysis);
    } else {
      return this.rejectTask(riskAnalysis);
    }
  }

  async autoExecute(blueprint) {
    console.log("⚡ [HANDS] High Confidence. Auto-executing...");
    await this.fs.applyChanges(blueprint.files);
    await this.fs.runTests(); // Self-healing check
    return { status: "merged", changed: Object.keys(blueprint.files) };
  }

  async createPullRequest(blueprint, riskAnalysis) {
    console.log("🤔 [HANDS] Medium Confidence. Creating Pull Request...");
    // In a real implementation, this would use a GitHub client to create a PR.
    // For now, we'll just log the intent.
    return { status: "pull_request_created", blueprint, riskAnalysis };
  }

  async rejectTask(riskAnalysis) {
    console.log("🛑 [HANDS] Low Confidence. Rejecting task...");
    // In a real implementation, this would notify the user or another system.
    return { status: "rejected", riskAnalysis };
  }
}
