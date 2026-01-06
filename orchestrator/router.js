const { KimiClient } = require('./clients/kimi');
const { FileSystemAgent } = require('./agents/fs');
const { ConfidenceScorer } = require('../tools/scorer');
const { SecurityGate } = require('./governance/security');
const { Octokit } = require("@octokit/rest");

class TaskRouter {
  constructor(config) {
    if (!process.env.GITHUB_TOKEN || process.env.GITHUB_TOKEN.trim() === '') {
        throw new Error('GITHUB_TOKEN environment variable must be set.');
    }
    this.kimi = new KimiClient(config.kimi);
    this.fs = new FileSystemAgent(config.fs);
    this.scorer = new ConfidenceScorer();
    this.security = new SecurityGate();
    this.octokit = new Octokit({ auth: process.env.GITHUB_TOKEN });
  }

  async handleRequest(intent) {
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

    // 4. Decision Matrix
    if (confidenceScore.score >= 90 && !riskAnalysis.hasCritical) {
      return this.applyAndTestChanges(blueprint);
    } else if (confidenceScore.score >= 70) {
      return this.createPullRequest(blueprint, riskAnalysis);
    } else {
      return this.rejectTask(riskAnalysis);
    }
  }

  async applyAndTestChanges(blueprint) {
    if (!blueprint || !Array.isArray(blueprint.files) || blueprint.files.length === 0) {
        return {
            status: "failed",
            changed: [],
            error: "Invalid blueprint or no files to apply."
        };
    }
    for (const file of blueprint.files) {
        if (!file.path || typeof file.path !== 'string') {
            return {
                status: "failed",
                changed: [],
                error: "Invalid file path in blueprint."
            };
        }
        if (!file.content && !file.deleted) {
            return {
                status: "failed",
                changed: [],
                error: "File must have content or be marked for deletion."
            };
        }
    }

    try {
        // In a real implementation, this would commit, push, and merge.
        await this.fs.applyChanges(blueprint.files);
        await this.fs.runTests(); // Self-healing check
        return { status: "merged", changed: Object.keys(blueprint.files) };
    } catch (err) {
        return {
            status: "failed",
            changed: [],
            error: err.message
        };
    }
  }

  async createPullRequest(blueprint, riskAnalysis) {
    const { owner, repo, base, head } = blueprint.branchInfo;

    const { data: pr } = await this.octokit.pulls.create({
      owner,
      repo,
      title: `[AI] ${blueprint.title}`,
      head,
      base,
      body: `
        ## AI-Generated Pull Request

        **Confidence Score:** ${riskAnalysis.score}/100

        **Risk Analysis:**
        \`\`\`json
        ${JSON.stringify(riskAnalysis, null, 2)}
        \`\`\`

        **Blueprint:**
        \`\`\`json
        ${JSON.stringify(blueprint, null, 2)}
        \`\`\`
      `,
    });

    return { status: "pull_request_created", pr_url: pr.html_url };
  }

  async rejectTask(riskAnalysis) {
    // In a real implementation, this would notify the user or another system.
    return { status: "rejected", riskAnalysis };
  }
}
