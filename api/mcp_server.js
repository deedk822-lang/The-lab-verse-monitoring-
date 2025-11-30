// api/mcp_server.js
import { spawn } from 'child_process';
import path from 'path';

export default async function handler(req, res) {
  if (req.method === 'POST') {
    const { command, args } = req.body;

    const mcpPath = path.resolve(process.cwd(), 'node_modules/.bin/mcp-wpcom-remote');
    const mcp = spawn(mcpPath, [command, ...args]);

    let stdout = '';
    let stderr = '';

    mcp.stdout.on('data', (data) => {
      stdout += data;
    });

    mcp.stderr.on('data', (data) => {
      stderr += data;
    });

    mcp.on('close', (code) => {
      if (code !== 0) {
        res.status(500).json({ error: stderr });
      } else {
        try {
          const result = JSON.parse(stdout);
          res.status(200).json(result);
        } catch (error) {
          res.status(500).json({ error: 'Failed to parse MCP server output' });
        }
      }
    });
  } else {
    res.status(405).json({ error: 'Method not allowed' });
  }
}
