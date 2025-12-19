import express from 'express';
import orchestrator from './api/orchestrator.js';
import provision from './api/models/provision.js';
import budgetAllocate from './api/hireborderless/budget-allocate.js';
import metricsHandler from './pages/api/metrics.js';

const app = express();
const port = 3000;

app.use(express.json());

app.post('/api/orchestrator', orchestrator);
app.post('/api/models/provision', provision);
app.post('/api/hireborderless/budget-allocate', budgetAllocate);

app.get('/api/metrics', metricsHandler);

app.listen(port, () => {
  console.log(`Server listening at http://localhost:${port}`);
});
