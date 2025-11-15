#!/usr/bin/env node
/**
 * MCP stdio server for Unito
 * Two-way sync between 60+ tools
 *
 * Install: npm i @modelcontextprotocol/sdk dotenv
 * Run: node unito-gateway.js
 */
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { CallToolRequestSchema, ListToolsRequestSchema } from '@modelcontextprotocol/sdk/types.js';
import dotenv from 'dotenv';

dotenv.config();

const GATEWAY_URL = process.env.GATEWAY_URL || process.env.VERCEL_URL
  ? `https://${process.env.VERCEL_URL}`
  : 'http://localhost:3000';
const GATEWAY_KEY = process.env.GATEWAY_KEY || process.env.UNITO_ACCESS_TOKEN;

if (!GATEWAY_KEY) {
  console.error('❌ Missing GATEWAY_KEY or UNITO_ACCESS_TOKEN');
  process.exit(1);
}

const server = new Server(
  { name: 'unito-gateway-mcp', version: '1.0.0' },
  { capabilities: { tools: {} } }
);

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: 'unito_list_workspaces',
      description: 'List all Unito workspaces',
      inputSchema: { type: 'object', properties: {} }
    },
    {
      name: 'unito_list_integrations',
      description: 'List all available connectors (60+ tools)',
      inputSchema: { type: 'object', properties: {} }
    },
    {
      name: 'unito_list_syncs',
      description: 'List syncs in a workspace',
      inputSchema: {
        type: 'object',
        properties: {
          workspaceId: { type: 'string', description: 'Workspace ID' }
        },
        required: ['workspaceId']
      }
    },
    {
      name: 'unito_create_sync',
      description: 'Create a new two-way sync',
      inputSchema: {
        type: 'object',
        properties: {
          workspaceId: { type: 'string', description: 'Workspace ID' },
          name: { type: 'string', description: 'Sync name' },
          description: { type: 'string', description: 'Sync description' },
          sourceConnector: { type: 'string', description: 'Source tool connector' },
          targetConnector: { type: 'string', description: 'Target tool connector' }
        },
        required: ['workspaceId', 'name']
      }
    },
    {
      name: 'unito_get_sync',
      description: 'Get sync details and statistics',
      inputSchema: {
        type: 'object',
        properties: {
          syncId: { type: 'string', description: 'Sync ID' }
        },
        required: ['syncId']
      }
    },
    {
      name: 'unito_update_sync',
      description: 'Update sync status (pause/resume/archive)',
      inputSchema: {
        type: 'object',
        properties: {
          syncId: { type: 'string', description: 'Sync ID' },
          status: {
            type: 'string',
            enum: ['active', 'paused', 'archived'],
            description: 'New sync status'
          }
        },
        required: ['syncId', 'status']
      }
    }
  ]
}));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    const body = {
      model: 'unito-mcp',
      messages: [{ role: 'user', content: `${name} ${JSON.stringify(args)}` }],
      stream: false
    };

    const response = await fetch(`${GATEWAY_URL}/mcp/unito/messages`, {
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
console.error('✅ Unito MCP Gateway started');
