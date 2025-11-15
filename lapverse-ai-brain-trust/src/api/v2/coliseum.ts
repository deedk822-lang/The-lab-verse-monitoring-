import { coliseumManager } from '../../coliseum/ColiseumManager';
import { z } from 'zod';

const createChallengeSchema = z.object({
  action: z.literal('create-challenge'),
  prompt: z.string(),
  priority: z.enum(['low', 'medium', 'high']).default('medium'),
  type: z.string().default('ai_analysis'),
});

const getLeaderboardSchema = z.object({
  action: z.literal('leaderboard'),
  challengeId: z.string(),
});

export const coliseumApi = {
  async post(query: unknown) {
    const parseResult = createChallengeSchema.safeParse(query);
    if (!parseResult.success) {
      return { status: 400, body: parseResult.error };
    }

    const { prompt, priority, type } = parseResult.data;
    const challengeId = await coliseumManager.createChallenge(
      `AI Battle: ${prompt.slice(0, 50)}…`,
      prompt,
      { prompt, query },
      priority,
      type
    );
    await coliseumManager.startBattle(challengeId);
    return { status: 200, body: { challengeId } };
  },

  async get(query: unknown) {
    const parseResult = getLeaderboardSchema.safeParse(query);
    if (!parseResult.success) {
      return { status: 400, body: parseResult.error };
    }

    const { challengeId } = parseResult.data;
    const history = coliseumManager.getBattleHistory(challengeId);
    return { status: 200, body: history };
  },
};