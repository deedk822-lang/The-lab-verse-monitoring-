/**
 * Vercel Intelligent Router
 * Implements the "Never-Fail" Workflow and Multi-Judge Fact-Checking Protocol
 * Based on the Final Blueprint for Autonomous Authority and Impact Engine
 */

import { AI_CONNECTIONS, JUDGE_ROLES, MISTRAL_MODELS } from './mistral-config';

export interface Message {
  role: 'system' | 'user' | 'assistant';
  content: string;
}

export interface FactCheckResult {
  claim: string;
  verdict: 'True' | 'False' | 'Inconclusive';
  confidence: number;
  evidence_url?: string;
  reasoning: string;
  judge: string;
}

export interface ConsensusResult {
  claim: string;
  finalVerdict: 'Fact-Checked: True' | 'Fact-Checked: False' | 'Fact-Checked: Inconclusive';
  consensus: string;
  judgeResults: FactCheckResult[];
  evidenceBlock: string;
}

/**
 * Generic AI model caller with OpenAI-compatible API
 */
async function callAIModel(
  provider: string,
  model: string,
  messages: Message[],
  apiKey: string,
  apiEndpoint?: string
): Promise<string> {
  const endpoint = apiEndpoint || 'https://api.openai.com/v1';

  try {
    const response = await fetch(`${endpoint}/chat/completions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiKey}`
      },
      body: JSON.stringify({
        model,
        messages,
        temperature: 0.7,
        max_tokens: 2048
      })
    });

    if (!response.ok) {
      throw new Error(`API call failed: ${response.status} ${response.statusText}`);
    }

    const data = await response.json();
    return data.choices[0]?.message?.content || '';
  } catch (error) {
    console.error(`Error calling ${provider} model ${model}:`, error);
    throw error;
  }
}

/**
 * Never-Fail Workflow: Generate content with automatic fallback
 */
export async function generateContentWithFallback(
  prompt: string,
  primaryModel: string = 'mixtral-8x22b-instruct',
  fallbackModel: string = 'glm-4'
): Promise<{ content: string; modelUsed: string; success: boolean }> {
  const messages: Message[] = [
    { role: 'user', content: prompt }
  ];

  // Try primary model (Mistral)
  try {
    console.log(`Attempting primary model: ${primaryModel}`);
    const content = await callAIModel(
      'mistral',
      primaryModel,
      messages,
      AI_CONNECTIONS.PRIMARY_GENERATOR.apiKey,
      AI_CONNECTIONS.PRIMARY_GENERATOR.apiEndpoint
    );

    return {
      content,
      modelUsed: primaryModel,
      success: true
    };
  } catch (primaryError) {
    console.warn(`Primary model failed, falling back to ${fallbackModel}:`, primaryError);

    // Fallback to GLM-4 or alternative
    try {
      const content = await callAIModel(
        'openai', // GLM-4 uses OpenAI-compatible API
        fallbackModel,
        messages,
        process.env.GLM_API_KEY || process.env.OPENAI_API_KEY || '',
        process.env.GLM_API_ENDPOINT || 'https://open.bigmodel.cn/api/paas/v4'
      );

      return {
        content,
        modelUsed: fallbackModel,
        success: true
      };
    } catch (fallbackError) {
      console.error('Both primary and fallback models failed:', fallbackError);
      return {
        content: 'Error: Unable to generate content. Both primary and fallback models failed.',
        modelUsed: 'none',
        success: false
      };
    }
  }
}

/**
 * Multi-Judge Fact-Checking Protocol
 * Uses three independent AI models to verify claims and establish consensus
 */
export async function factCheckClaim(
  claim: string,
  searchResults?: string[]
): Promise<ConsensusResult> {
  const judgeKeys = Object.keys(AI_CONNECTIONS).filter(key => key.startsWith('FACT_CHECK_JUDGE'));
  const judges = judgeKeys.map(key => {
    const role = key.split('_').pop() as keyof typeof JUDGE_ROLES;
    return {
      name: `Judge ${role}`,
      config: AI_CONNECTIONS[key],
      systemPrompt: JUDGE_ROLES[role]?.systemPrompt || 'You are an independent fact-checking judge.'
    };
  });

  const judgeResults: FactCheckResult[] = [];

  // Context for fact-checking
  const context = searchResults
    ? `\n\nSearch Results:\n${searchResults.join('\n\n')}`
    : '';

  // Execute fact-checking in parallel with all three judges
  const factCheckPromises = judges.map(async (judge) => {
    const messages: Message[] = [
      {
        role: 'system',
        content: `${judge.systemPrompt}

Respond in JSON format:
{
  "verdict": "True|False|Inconclusive",
  "confidence": 85,
  "evidence_url": "https://...",
  "reasoning": "..."
}`
      },
      {
        role: 'user',
        content: `Claim: "${claim}"${context}\n\nProvide your fact-check verdict in JSON format.`
      }
    ];

    try {
      const response = await callAIModel(
        judge.config.provider,
        judge.config.model,
        messages,
        judge.config.apiKey,
        judge.config.apiEndpoint
      );

      // Parse JSON response
      const jsonMatch = response.match(/\{[\s\S]*\}/);
      if (jsonMatch) {
        const parsed = JSON.parse(jsonMatch[0]);
        return {
          claim,
          verdict: parsed.verdict || 'Inconclusive',
          confidence: parsed.confidence || 0,
          evidence_url: parsed.evidence_url,
          reasoning: parsed.reasoning || 'No reasoning provided',
          judge: judge.name
        } as FactCheckResult;
      }

      // Fallback if JSON parsing fails
      return {
        claim,
        verdict: 'Inconclusive' as const,
        confidence: 0,
        reasoning: 'Failed to parse judge response',
        judge: judge.name
      };
    } catch (error) {
      console.error(`Judge ${judge.name} failed:`, error);
      return {
        claim,
        verdict: 'Inconclusive' as const,
        confidence: 0,
        reasoning: `Error: ${error instanceof Error ? error.message : 'Unknown error'}`,
        judge: judge.name
      };
    }
  });

  judgeResults.push(...await Promise.all(factCheckPromises));

  // Consensus Protocol: Require at least 2 out of 3 judges to agree
  const trueCount = judgeResults.filter(r => r.verdict === 'True').length;
  const falseCount = judgeResults.filter(r => r.verdict === 'False').length;

  let finalVerdict: ConsensusResult['finalVerdict'];
  let consensus: string;

  if (trueCount >= 2) {
    finalVerdict = 'Fact-Checked: True';
    consensus = `Consensus: ${trueCount}/3 judges agree`;
  } else if (falseCount >= 2) {
    finalVerdict = 'Fact-Checked: False';
    consensus = `Consensus: ${falseCount}/3 judges agree`;
  } else {
    finalVerdict = 'Fact-Checked: Inconclusive';
    consensus = 'No consensus reached (judges disagree)';
  }

  // Generate Evidence Block
  const evidenceBlock = generateEvidenceBlock(claim, judgeResults, finalVerdict, consensus);

  return {
    claim,
    finalVerdict,
    consensus,
    judgeResults,
    evidenceBlock
  };
}

/**
 * Generate Markdown evidence block for transparency
 */
function generateEvidenceBlock(
  claim: string,
  judgeResults: FactCheckResult[],
  finalVerdict: string,
  consensus: string
): string {
  let markdown = `### Fact-Check Evidence for Claim: "${claim}"\n\n`;
  markdown += `| Judge Agent | Verdict | Confidence | Supporting Evidence |\n`;
  markdown += `| :--- | :--- | :--- | :--- |\n`;

  for (const result of judgeResults) {
    const evidenceLink = result.evidence_url
      ? `[Source](${result.evidence_url})`
      : 'No URL provided';
    markdown += `| ${result.judge} | ${result.verdict} | ${result.confidence}% | ${evidenceLink} |\n`;
  }

  markdown += `\n**Final Verdict:** ${finalVerdict} (${consensus})\n\n`;

  markdown += `**Reasoning Summary:**\n`;
  for (const result of judgeResults) {
    markdown += `- **${result.judge}**: ${result.reasoning}\n`;
  }

  return markdown;
}

/**
 * Extract factual claims from generated content
 */
export async function extractClaims(content: string): Promise<string[]> {
  const messages: Message[] = [
    {
      role: 'system',
      content: 'You are a claim extraction assistant. Extract all factual claims from the given content. Return only a JSON array of claims.'
    },
    {
      role: 'user',
      content: `Extract factual claims from this content:\n\n${content}\n\nReturn JSON array: ["claim1", "claim2", ...]`
    }
  ];

  try {
    const response = await callAIModel(
      AI_CONNECTIONS.PRIMARY_GENERATOR.provider,
      AI_CONNECTIONS.PRIMARY_GENERATOR.model,
      messages,
      AI_CONNECTIONS.PRIMARY_GENERATOR.apiKey,
      AI_CONNECTIONS.PRIMARY_GENERATOR.apiEndpoint
    );

    const jsonMatch = response.match(/\[[\s\S]*\]/);
    if (jsonMatch) {
      return JSON.parse(jsonMatch[0]);
    }
    return [];
  } catch (error) {
    console.error('Failed to extract claims:', error);
    return [];
  }
}

/**
 * Complete workflow: Generate content with fact-checking
 */
export async function generateFactCheckedContent(
  prompt: string,
  enableFactCheck: boolean = true
): Promise<{
  content: string;
  modelUsed: string;
  factChecks?: ConsensusResult[];
  success: boolean;
}> {
  // Step 1: Generate content
  const generation = await generateContentWithFallback(prompt);

  if (!generation.success || !enableFactCheck) {
    return {
      ...generation,
      factChecks: []
    };
  }

  // Step 2: Extract claims
  const claims = await extractClaims(generation.content);

  if (claims.length === 0) {
    return {
      ...generation,
      factChecks: []
    };
  }

  // Step 3: Fact-check each claim
  const factCheckPromises = claims.slice(0, 5).map(claim => factCheckClaim(claim)); // Limit to 5 claims
  const factChecks = await Promise.all(factCheckPromises);

  // Step 4: Append evidence blocks to content
  let enhancedContent = generation.content;
  enhancedContent += '\n\n---\n\n## Fact-Check Evidence\n\n';
  for (const factCheck of factChecks) {
    enhancedContent += factCheck.evidenceBlock + '\n\n';
  }

  return {
    content: enhancedContent,
    modelUsed: generation.modelUsed,
    factChecks,
    success: true
  };
}

export default {
  generateContentWithFallback,
  factCheckClaim,
  extractClaims,
  generateFactCheckedContent
};
