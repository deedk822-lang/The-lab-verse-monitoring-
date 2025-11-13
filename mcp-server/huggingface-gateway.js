#!/usr/bin/env node
/*  MCP stdio server → forwards HF hub / inference calls → your universal gateway
 *  Install:  npm i @modelcontextprotocol/sdk commander dotenv
 *  Run:      node huggingface-gateway.js
 */
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { CallToolRequestSchema, ListToolsRequestSchema } from '@modelcontextprotocol/sdk/types.js';
import dotenv from 'dotenv';
dotenv.config();

const GATEWAY_URL = process.env.GATEWAY_URL || 'https://<your-domain>';
const GATEWAY_KEY = process.env.GATEWAY_KEY || process.env.HF_API_TOKEN;

const server = new Server(
  { name: 'huggingface-gateway-mcp', version: '1.0.0' },
  { capabilities: { tools: {} } }
);

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    { name: 'hf_list_models',     description: 'Search HF models', inputSchema: { type: 'object', properties: { search: { type: 'string' }, limit: { type: 'number' } } } },
    { name: 'hf_model_info',      description: 'Get model card & stats', inputSchema: { type: 'object', properties: { model: { type: 'string' } }, required: ['model'] } },
    { name: 'hf_list_datasets',   description: 'Search HF datasets', inputSchema: { type: 'object', properties: { search: { type: 'string' }, limit: { type: 'number' } } } },
    { name: 'hf_list_spaces',     description: 'Search HF Spaces', inputSchema: { type: 'object', properties: { search: { type: 'string' }, limit: { type: 'number' } } } },
    { name: 'hf_run_inference',   description: 'Run serverless inference', inputSchema: { type: 'object', properties: { model: { type: 'string' }, inputs: { type: 'string' }, params: { type: 'string' } }, required: ['model', 'inputs'] } },
  ]
}));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;
  const body = {
    model: 'hf-mcp',
    messages: [{ role: 'user', content: `${name} ${JSON.stringify(args)}` }],
    stream: false,
  };

  const res = await fetch(`${GATEWAY_URL}/mcp/huggingface/messages`, {
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
