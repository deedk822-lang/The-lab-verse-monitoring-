import { tongyiDeepResearch } from './providers/tongyi';
import { coliseumManager } from '../coliseum/ColiseumManager';

export const connectAI = async (prompt: string, opts: any = {}) => {
  if (opts.enableColiseum) return handleWithColiseum(prompt, opts);
  // …existing quad-brain logic…
  // For now, just return a simple response
  return { default: `Response for: ${prompt}` };
};

async function handleWithColiseum(prompt: string, opts: any) {
  const challenge = await coliseumManager.createChallenge(
    `AI Battle: ${prompt.slice(0, 50)}…`,
    prompt,
    { prompt, opts },
    'medium',
    'ai_analysis'
  );
  await coliseumManager.startBattle(challenge);
  const [result] = coliseumManager.getBattleHistory(challenge);
  const winner = coliseumManager.getCompetitor(result.winner);
  return {
    [winner.type]: result.results[result.winner],
    metadata: { coliseum: result }
  };
}

export const performDeepResearch = async (query: string, type: any, opts: any) =>
  tongyiDeepResearch.analyzeAnomaly({ query, researchType: type }, opts);