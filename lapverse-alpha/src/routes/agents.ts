import { Router } from 'express';
import { agentOrchestrator } from '../agents/AgentOrchestrator';

const router = Router();

router.get('/', (req, res) => {
  const agents = agentOrchestrator.getAllAgents();
  res.json(agents);
});

router.post('/tasks', async (req, res) => {
  try {
    const { type, prompt } = req.body;
    const taskId = await agentOrchestrator.createTask(type, prompt);
    res.json({ taskId });
  } catch (error) {
    res.status(500).json({ error: error instanceof Error ? error.message : 'Unknown error' });
  }
});

router.get('/tasks/:taskId', (req, res) => {
  const task = agentOrchestrator.getTask(req.params.taskId);
  if (!task) {
    return res.status(404).json({ error: 'Task not found' });
  }
  res.json(task);
});

export { router as agentRoutes };