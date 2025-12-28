// app.js - FIXED
import express from 'express';

// ✅ REMOVED: Dead imports
// import webhookHandler from './api/webhook.js';  // File doesn't exist
// import mcpHandler from './api/mcp_server.js';   // File doesn't exist

const app = express();
const port = 7860;

// Basic middleware
app.use(express.json());

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ status: 'healthy', port });
});

// ✅ TODO: Create these handlers if needed:
// app.use('/api/webhook', webhookHandler);
// app.use('/api/mcp', mcpHandler);

app.listen(port, () => {
  console.log(`✅ App server running on port ${port}`);
});

export default app;
