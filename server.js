const express = require('express');
const orchestrator = require('./api/orchestrator.js');
const provision = require('./api/models/provision.js');
const budgetAllocate = require('./api/hireborderless/budget-allocate.js');

const app = express();
const port = 3000;

app.use(express.json());

app.post('/api/orchestrator', orchestrator);
app.post('/api/models/provision', provision);
app.post('/api/hireborderless/budget-allocate', budgetAllocate);

app.listen(port, () => {
  console.log(`Server listening at http://localhost:${port}`);
});
