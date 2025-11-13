#!/usr/bin/env node
/*  MCP stdio server → forwards Unito tool-calls → your universal gateway
 *  Install:  npm i @modelcontextprotocol/sdk commander dotenv
 *  Run:      node unito-gateway.js
 */
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { CallToolRequestSchema, ListToolsRequestSchema } from '@modelcontextprotocol/sdk/types.js';
import dotenv from 'dotenv';
dotenv.config();

const GATEWAY_URL = process.env.GATEWAY_URL || 'https://<your-domain>';
const GATEWAY_KEY = process.env.GATEWAY_KEY || process.env.UNITO_ACCESS_TOKEN;

const server = new Server(
  { name: 'unito-gateway-mcp', version: '1.0.0' },
  { capabilities: { tools: {} } }
);

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    { name: 'unito_list_workspaces', description: 'List all Unito workspaces' },
    { name: 'unito_list_integrations', description: 'List all 60+ connectors available in Unito' },
    { name: 'unito_list_syncs', description: 'List syncs inside a workspace', inputSchema: { type: 'object', properties: { workspace: { type: 'string' } }, required: ['workspace'] } },
    { name: 'unito_create_sync', description: 'Create a new sync between two tools', inputSchema: { type: 'object', properties: { workspace: { type: 'string' }, name: { type: 'string' }, description: { type: 'string' } }, required: ['workspace', 'name'] } },
    { name: 'unito_get_sync', description: 'Get details of a specific sync', inputSchema: { type: 'object', properties: { sync: { type: 'string' } }, required: ['sync'] } },
    { name: 'unito_update_sync', description: 'Pause / resume / archive a sync', inputSchema: { type: 'object', properties: { sync: { type: 'string' }, status: { type: 'string', enum: ['active', 'paused', 'archived'] } }, required: ['sync', 'status'] } },
  ]
}));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;
  const body = {
    model: 'unito-mcp',
    messages: [{ role: 'user', content: `${name} ${JSON.stringify(args)}` }],
    stream: false,
  };

  const res = await fetch(`${GATEWAY_URL}/mcp/unito/messages`, {
    method: 'POST',
    headers: {
      'content-type': 'application/json',
      authorization: `Bearer ${GATEWAY_KEY}`,
    },
    body: JSON.stringify(body),
  });

  if (!res.ok) throw new Error(`Gateway ${res.status}: ${await res.text()}`);
  const json = await res.json();
  const text = json.choices?.[0]?.message?.content || '';
  return { content: [{ type: 'text', text }] };
});

const transport = new StdioServerTransport();
await server.connect(transport);
