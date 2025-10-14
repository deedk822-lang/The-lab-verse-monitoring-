import { Router } from 'express';
import { coliseumManager } from '../../coliseum/ColiseumManager';
import { z } from 'zod';

const router = Router();

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

router.post('/', async (req, res) => {
  const parseResult = createChallengeSchema.safeParse(req.query);
  if (!parseResult.success) {
    return res.status(400).json(parseResult.error);
  }

  const { prompt, priority, type } = parseResult.data;
  const challengeId = await coliseumManager.createChallenge(
    `AI Battle: ${prompt.slice(0, 50)}…`,
    prompt,
    { prompt, query: req.query },
    priority,
    type
  );
  await coliseumManager.startBattle(challengeId);
  res.json({ challengeId });
});

router.get('/', (req, res) => {
  const parseResult = getLeaderboardSchema.safeParse(req.query);
  if (!parseResult.success) {
    return res.status(400).json(parseResult.error);
  }

  const { challengeId } = parseResult.data;
  const history = coliseumManager.getBattleHistory(challengeId);
  res.json(history);
});

export default router;