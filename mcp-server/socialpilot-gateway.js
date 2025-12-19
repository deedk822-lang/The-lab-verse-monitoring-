#!/usr/bin/env node
/**
 * MCP stdio server for SocialPilot
 * Manages social media scheduling and analytics
 *
 * Install: npm i @modelcontextprotocol/sdk dotenv
 * Run: node socialpilot-gateway.js
 */
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { CallToolRequestSchema, ListToolsRequestSchema } from '@modelcontextprotocol/sdk/types.js';
import dotenv from 'dotenv';

dotenv.config();

const GATEWAY_URL = process.env.GATEWAY_URL || process.env.VERCEL_URL
  ? `https://${process.env.VERCEL_URL}`
  : 'http://localhost:3000';
const GATEWAY_KEY = process.env.GATEWAY_KEY || process.env.SOCIALPILOT_ACCESS_TOKEN;

if (!GATEWAY_KEY) {
  console.error('❌ Missing GATEWAY_KEY or SOCIALPILOT_ACCESS_TOKEN');
  process.exit(1);
}

const server = new Server(
  { name: 'socialpilot-gateway-mcp', version: '1.0.0' },
  { capabilities: { tools: {} } }
);

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: 'sp_list_accounts',
      description: 'List all connected social media accounts',
      inputSchema: { type: 'object', properties: {} }
    },
    {
      name: 'sp_create_post',
      description: 'Schedule a social media post',
      inputSchema: {
        type: 'object',
        properties: {
          message: { type: 'string', description: 'Post content' },
          accounts: { type: 'string', description: 'Comma-separated account IDs' },
          scheduledTime: { type: 'string', description: 'ISO 8601 timestamp or "now"' },
          media: { type: 'array', items: { type: 'string' }, description: 'Media URLs' }
        },
        required: ['message', 'accounts']
      }
    },
    {
      name: 'sp_get_analytics',
      description: 'Get post performance analytics',
      inputSchema: {
        type: 'object',
        properties: {
          account: { type: 'string', description: 'Account ID' },
          startDate: { type: 'string', description: 'Start date (YYYY-MM-DD)' },
          endDate: { type: 'string', description: 'End date (YYYY-MM-DD)' }
        },
        required: ['account']
      }
    },
    {
      name: 'sp_list_queues',
      description: 'List all queued and scheduled posts',
      inputSchema: { type: 'object', properties: {} }
    },
    {
      name: 'sp_delete_post',
      description: 'Delete a scheduled post',
      inputSchema: {
        type: 'object',
        properties: {
          postId: { type: 'string', description: 'Post ID to delete' }
        },
        required: ['postId']
      }
    }
  ]
}));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    const body = {
      model: 'socialpilot-mcp',
      messages: [{ role: 'user', content: `${name} ${JSON.stringify(args)}` }],
      stream: false
    };

    const response = await fetch(`${GATEWAY_URL}/mcp/socialpilot/messages`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${GATEWAY_KEY}`
      },
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(30000)
    });

    if (!response.ok) {
      throw new Error(`Gateway ${response.status}: ${await response.text()}`);
    }

    const json = await response.json();
    const text = json.choices?.[0]?.message?.content || JSON.stringify(json);

    return { content: [{ type: 'text', text }] };

  } catch (error) {
    console.error(`❌ Tool execution failed: ${error.message}`);
    return {
      content: [{ type: 'text', text: `Error: ${error.message}` }],
      isError: true
    };
  }
});

const transport = new StdioServerTransport();
await server.connect(transport);
console.error('✅ SocialPilot MCP Gateway started');
