// server.js - FIXED
import express from 'express';
import orchestrator from './api/orchestrator.js';
import provision from './api/models/provision.js';
import budgetAllocate from './api/hireborderless/budget-allocate.js';

// ✅ BOTH features integrated properly
import { initializeSpeedInsights, speedInsightsMiddleware } from './lib/speed-insights.js';
import metricsHandler from './pages/api/metrics.js';

const app = express();
const port = process.env.PORT || 3000;

// Initialize Speed Insights
initializeSpeedInsights();

// Apply middleware
app.use(express.json());
app.use(speedInsightsMiddleware);

// Routes
app.use('/api/orchestrator', orchestrator);
app.use('/api/provision', provision);
app.use('/api/budget-allocate', budgetAllocate);
app.use('/api/metrics', metricsHandler);

app.listen(port, () => {
  console.log(`✅ Server running on port ${port}`);
});

export default app;
