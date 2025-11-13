#!/usr/bin/env node
/*  MCP stdio server → forwards SocialPilot tool-calls → your universal gateway
 *  Install:  npm i @modelcontextprotocol/sdk commander dotenv
 *  Run:      node socialpilot-gateway.js
 */
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { CallToolRequestSchema, ListToolsRequestSchema } from '@modelcontextprotocol/sdk/types.js';
import dotenv from 'dotenv';
dotenv.config();

const GATEWAY_URL = process.env.GATEWAY_URL || 'https://<your-domain>';
const GATEWAY_KEY = process.env.GATEWAY_KEY || process.env.SOCIALPILOT_ACCESS_TOKEN;

const server = new Server(
  { name: 'socialpilot-gateway-mcp', version: '1.0.0' },
  { capabilities: { tools: {} } }
);

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    { name: 'sp_list_accounts',   description: 'List connected social accounts' },
    { name: 'sp_create_post',     description: 'Schedule a post', inputSchema: { type: 'object', properties: { message: { type: 'string' }, accounts: { type: 'string' }, when: { type: 'string' } }, required: ['message', 'accounts'] } },
    { name: 'sp_get_analytics',   description: 'Get post analytics for an account', inputSchema: { type: 'object', properties: { account: { type: 'string' } }, required: ['account'] } },
    { name: 'sp_list_queues',     description: 'List queued posts' },
  ]
}));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;
  const body = {
    model: 'socialpilot-mcp',
    messages: [{ role: 'user', content: `${name} ${JSON.stringify(args)}` }],
    stream: false,
  };

  const res = await fetch(`${GATEWAY_URL}/mcp/socialpilot/messages`, {
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
