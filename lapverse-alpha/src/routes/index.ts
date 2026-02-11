import { Router } from 'express';
import { agentRoutes } from './agents';
import { coliseumRoutes } from './coliseum';
// import { a2aRoutes } from './a2a';
// import { argillaRoutes } from './argilla';

const router = Router();

router.use('/agents', agentRoutes);
router.use('/coliseum', coliseumRoutes);
// router.use('/a2a', a2aRoutes);
// router.use('/argilla', argillaRoutes);

export default router;