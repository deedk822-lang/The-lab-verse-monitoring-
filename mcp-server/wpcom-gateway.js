#!/usr/bin/env node
/*  MCP stdio server → forwards WP.com tool-calls → your universal gateway
 *  Install:  npm i @modelcontextprotocol/sdk commander dotenv
 *  Run:      node wpcom-gateway.js
 */
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { CallToolRequestSchema, ListToolsRequestSchema } from '@modelcontextprotocol/sdk/types.js';
import dotenv from 'dotenv';
dotenv.config();

const GATEWAY_URL = process.env.GATEWAY_URL || 'https://<your-domain>';
const GATEWAY_KEY = process.env.GATEWAY_KEY || process.env.WORDPRESS_COM_OAUTH_TOKEN;

const server = new Server(
  { name: 'wpcom-gateway-mcp', version: '1.0.0' },
  { capabilities: { tools: {} } }
);

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    { name: 'wpcom_list_sites',      description: 'List all WordPress.com sites' },
    { name: 'wpcom_create_post',     description: 'Create a new post', inputSchema: { type: 'object', properties: { site: { type: 'string' }, title: { type: 'string' }, content: { type: 'string' }, status: { type: 'string', enum: ['draft', 'publish'], default: 'draft' } }, required: ['site', 'title', 'content'] } },
    { name: 'wpcom_list_posts',      description: 'List posts for a site', inputSchema: { type: 'object', properties: { site: { type: 'string' } }, required: ['site'] } },
    { name: 'wpcom_get_post',        description: 'Get single post', inputSchema: { type: 'object', properties: { site: { type: 'string' }, post_id: { type: 'string' } }, required: ['site', 'post_id'] } },
    { name: 'wpcom_update_post',     description: 'Update post status', inputSchema: { type: 'object', properties: { site: { type: 'string' }, post_id: { type: 'string' }, status: { type: 'string', enum: ['draft', 'publish', 'trash'] } }, required: ['site', 'post_id', 'status'] } },
  ]
}));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;
  const body = {
    model: 'wpcom-mcp',
    messages: [{ role: 'user', content: `${name} ${JSON.stringify(args)}` }],
    stream: false,
  };

  const res = await fetch(`${GATEWAY_URL}/mcp/wpcom/messages`, {
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
