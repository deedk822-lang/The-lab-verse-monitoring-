#!/usr/bin/env node
/**
 * MCP stdio server for WordPress.com
 * Manage posts, pages, and sites
 *
 * Install: npm i @modelcontextprotocol/sdk dotenv
 * Run: node wpcom-gateway.js
 */
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { CallToolRequestSchema, ListToolsRequestSchema } from '@modelcontextprotocol/sdk/types.js';
import dotenv from 'dotenv';

dotenv.config();

const GATEWAY_URL = process.env.GATEWAY_URL || process.env.VERCEL_URL
  ? `https://${process.env.VERCEL_URL}`
  : 'http://localhost:3000';
const GATEWAY_KEY = process.env.GATEWAY_KEY || process.env.WORDPRESS_COM_OAUTH_TOKEN;

if (!GATEWAY_KEY) {
  console.error('❌ Missing GATEWAY_KEY or WORDPRESS_COM_OAUTH_TOKEN');
  process.exit(1);
}

const server = new Server(
  { name: 'wpcom-gateway-mcp', version: '1.0.0' },
  { capabilities: { tools: {} } }
);

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: 'wpcom_list_sites',
      description: 'List all WordPress.com sites',
      inputSchema: { type: 'object', properties: {} }
    },
    {
      name: 'wpcom_create_post',
      description: 'Create a new blog post',
      inputSchema: {
        type: 'object',
        properties: {
          site: { type: 'string', description: 'Site ID or domain' },
          title: { type: 'string', description: 'Post title' },
          content: { type: 'string', description: 'Post content (HTML)' },
          status: {
            type: 'string',
            enum: ['draft', 'publish', 'private'],
            default: 'draft',
            description: 'Post status'
          },
          categories: { type: 'array', items: { type: 'string' } },
          tags: { type: 'array', items: { type: 'string' } }
        },
        required: ['site', 'title', 'content']
      }
    },
    {
      name: 'wpcom_list_posts',
      description: 'List posts for a site',
      inputSchema: {
        type: 'object',
        properties: {
          site: { type: 'string', description: 'Site ID or domain' },
          status: { type: 'string', enum: ['draft', 'publish', 'all'] },
          limit: { type: 'number', default: 20 }
        },
        required: ['site']
      }
    },
    {
      name: 'wpcom_get_post',
      description: 'Get a single post by ID',
      inputSchema: {
        type: 'object',
        properties: {
          site: { type: 'string', description: 'Site ID or domain' },
          postId: { type: 'string', description: 'Post ID' }
        },
        required: ['site', 'postId']
      }
    },
    {
      name: 'wpcom_update_post',
      description: 'Update an existing post',
      inputSchema: {
        type: 'object',
        properties: {
          site: { type: 'string', description: 'Site ID or domain' },
          postId: { type: 'string', description: 'Post ID' },
          title: { type: 'string', description: 'New title' },
          content: { type: 'string', description: 'New content' },
          status: { type: 'string', enum: ['draft', 'publish', 'trash'] }
        },
        required: ['site', 'postId']
      }
    },
    {
      name: 'wpcom_delete_post',
      description: 'Delete a post',
      inputSchema: {
        type: 'object',
        properties: {
          site: { type: 'string', description: 'Site ID or domain' },
          postId: { type: 'string', description: 'Post ID' }
        },
        required: ['site', 'postId']
      }
    }
  ]
}));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    const body = {
      model: 'wpcom-mcp',
      messages: [{ role: 'user', content: `${name} ${JSON.stringify(args)}` }],
      stream: false
    };

    const response = await fetch(`${GATEWAY_URL}/mcp/wpcom/messages`, {
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
console.error('✅ WordPress.com MCP Gateway started');
