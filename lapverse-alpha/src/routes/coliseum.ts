import { Router } from 'express';
import { coliseumManager } from '../coliseum/ColiseumManager';

const router = Router();

router.post('/battles', async (req, res) => {
  try {
    const { competitors, prompt, category, severity } = req.body;
    const battleId = await coliseumManager.createBattle(competitors, prompt, category, severity);
    res.json({ battleId });
  } catch (error) {
    res.status(500).json({ error: error instanceof Error ? error.message : 'Unknown error' });
  }
});

router.post('/battles/:battleId/start', async (req, res) => {
  try {
    await coliseumManager.startBattle(req.params.battleId);
    res.json({ success: true });
  } catch (error) {
    res.status(500).json({ error: error instanceof Error ? error.message : 'Unknown error' });
  }
});

router.get('/battles/:battleId', (req, res) => {
  const battle = coliseumManager.getBattle(req.params.battleId);
  if (!battle) {
    return res.status(404).json({ error: 'Battle not found' });
  }
  res.json(battle);
});

router.get('/battles', (req, res) => {
  const battles = coliseumManager.getAllBattles();
  res.json(battles);
});

export { router as coliseumRoutes };