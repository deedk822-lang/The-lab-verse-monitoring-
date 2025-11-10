
import express from 'express';
import webhookHandler from './api/webhook.js';
import mcpHandler from './api/mcp_server.js';

const app = express();
const port = 7860;

// Middleware to parse JSON bodies
app.use(express.json());

// Route for the webhook
app.post('/api/webhook', webhookHandler);

// Route for the MCP server
app.post('/api/mcp', mcpHandler);

// Root endpoint for health checks
app.get('/', (req, res) => {
  res.status(200).json({ message: 'RankYak Bridge alive', endpoint: '/api/webhook' });
});

app.listen(port, () => {
  console.log(`Server listening at http://localhost:${port}`);
});
