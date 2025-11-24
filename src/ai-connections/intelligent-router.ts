// src/ai-connections/intelligent-router.ts
import { mistralModels, supportingModels, fallbackModel } from './mistral-config';
import { OpenAI } from 'openai';

const getClient = (provider: string, apiKey: string, baseURL?: string) => {
  return new OpenAI({ apiKey, baseURL });
};

export async function generateContent(prompt: string, primaryModel: keyof typeof mistralModels, fallbackModelName: keyof typeof fallbackModel) {
  const primary = mistralModels[primaryModel];
  const fallback = fallbackModel[fallbackModelName];

  try {
    const client = getClient(primary.provider, process.env.MISTRAL_API_KEY as string, 'https://api.mistral.ai/v1/');
    const response = await client.chat.completions.create({
      model: primary.model,
      messages: [{ role: 'user', content: prompt }],
    });
    return {
      success: true,
      content: response.choices[0].message.content,
      modelUsed: primary.model,
    };
  } catch (error) {
    console.warn(`Primary model '${primary.model}' failed. Initiating fallback to '${fallback.model}'.`, error);
    try {
      const client = getClient(fallback.provider, process.env.GLM_API_KEY as string, process.env.GLM_API_ENDPOINT);
      const response = await client.chat.completions.create({
        model: fallback.model,
        messages: [{ role: 'user', content: prompt }],
      });
      return {
        success: true,
        content: response.choices[0].message.content,
        modelUsed: fallback.model,
      };
    } catch (fallbackError) {
      console.error('FATAL: Primary and Fallback models both failed.', fallbackError);
      return { success: false, content: null, modelUsed: null };
    }
  }
}

export async function factCheckClaim(claim: string, searchResults: string[]) {
  const judges = [
    { name: 'Judge Gemini', model: supportingModels.gemini, client: getClient('google', process.env.GEMINI_API_KEY as string, 'https://generativelanguage.googleapis.com/v1beta/models/') },
    { name: 'Judge Groq', model: supportingModels.groq, client: getClient('groq', process.env.GROQ_API_KEY as string, 'https://api.groq.com/openai/v1/') },
    { name: 'Judge Claude', model: supportingModels.claude, client: getClient('anthropic', process.env.ANTHROPIC_API_KEY as string, 'https://api.anthropic.com/v1/') },
  ];

  const verdicts = await Promise.all(judges.map(async (judge) => {
    try {
      const response = await judge.client.chat.completions.create({
        model: judge.model.model,
        messages: [
          { role: 'system', content: `You are a fact-checking judge. Evaluate the claim based on the provided search results. Respond with a JSON object containing "verdict" (True/False/Inconclusive), "confidence" (0-100), "evidence_url", and "reasoning".` },
          { role: 'user', content: `Claim: "${claim}"\n\nSearch Results:\n${searchResults.join('\n')}` },
        ],
      });
      const result = JSON.parse(response.choices[0].message.content || '{}');
      return { ...result, judge: judge.name };
    } catch (error) {
      return { verdict: 'Error', judge: judge.name, reasoning: (error as Error).message };
    }
  }));

  const trueCount = verdicts.filter(v => v.verdict === 'True').length;
  const finalVerdict = trueCount >= 2 ? 'Fact-Checked: True' : 'Fact-Checked: False/Inconclusive';

  const evidenceBlock = `### Fact-Check Evidence for Claim: "${claim}"\n\n| Judge Agent | Verdict | Supporting Evidence |\n| :--- | :--- | :--- |\n${verdicts.map(v => `| **${v.judge}** | ${v.verdict} | [Source](${v.evidence_url}) |`).join('\n')}\n\n**Final Verdict:** **${finalVerdict}** (Consensus: ${trueCount}/3)`;

  return {
    claim,
    finalVerdict,
    consensus: `Consensus: ${trueCount}/3 judges agree`,
    judgeResults: verdicts,
    evidenceBlock,
  };
}
