#!/usr/bin/env node
/**
 * MCP stdio server for HuggingFace Hub & Inference API
 * Forwards tool calls to your universal gateway
 *
 * Install: npm i @modelcontextprotocol/sdk dotenv
 * Run: node huggingface-gateway.js
 */
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { CallToolRequestSchema, ListToolsRequestSchema } from '@modelcontextprotocol/sdk/types.js';
import dotenv from 'dotenv';

dotenv.config();

// Configuration with validation
const GATEWAY_URL = process.env.GATEWAY_URL || process.env.VERCEL_URL
  ? `https://${process.env.VERCEL_URL}`
  : 'http://localhost:3000';
const GATEWAY_KEY = process.env.GATEWAY_KEY || process.env.HF_API_TOKEN;

if (!GATEWAY_KEY) {
  console.error('❌ Missing GATEWAY_KEY or HF_API_TOKEN environment variable');
  process.exit(1);
}

// Initialize MCP server
const server = new Server(
  {
    name: 'huggingface-gateway-mcp',
    version: '1.0.0'
  },
  {
    capabilities: { tools: {} }
  }
);

// Tool definitions
server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: 'hf_list_models',
      description: 'Search HuggingFace models by keyword',
      inputSchema: {
        type: 'object',
        properties: {
          search: { type: 'string', description: 'Search query' },
          limit: { type: 'number', default: 10, description: 'Max results' }
        }
      }
    },
    {
      name: 'hf_model_info',
      description: 'Get detailed model information and stats',
      inputSchema: {
        type: 'object',
        properties: {
          model: { type: 'string', description: 'Model ID (e.g., gpt2)' }
        },
        required: ['model']
      }
    },
    {
      name: 'hf_list_datasets',
      description: 'Search HuggingFace datasets',
      inputSchema: {
        type: 'object',
        properties: {
          search: { type: 'string', description: 'Search query' },
          limit: { type: 'number', default: 10 }
        }
      }
    },
    {
      name: 'hf_list_spaces',
      description: 'Search HuggingFace Spaces (apps & demos)',
      inputSchema: {
        type: 'object',
        properties: {
          search: { type: 'string', description: 'Search query' },
          limit: { type: 'number', default: 10 }
        }
      }
    },
    {
      name: 'hf_run_inference',
      description: 'Run serverless inference on a model',
      inputSchema: {
        type: 'object',
        properties: {
          model: { type: 'string', description: 'Model ID' },
          inputs: { type: 'string', description: 'Input text or data' },
          parameters: { type: 'object', description: 'Inference parameters' }
        },
        required: ['model', 'inputs']
      }
    }
  ]
}));

// Tool execution handler
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    const body = {
      model: 'hf-mcp',
      messages: [
        {
          role: 'user',
          content: `${name} ${JSON.stringify(args)}`
        }
      ],
      stream: false
    };

    const response = await fetch(`${GATEWAY_URL}/mcp/huggingface/messages`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${GATEWAY_KEY}`
      },
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(30000) // 30s timeout
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Gateway ${response.status}: ${errorText}`);
    }

    const json = await response.json();
    const text = json.choices?.[0]?.message?.content || JSON.stringify(json);

    return {
      content: [{ type: 'text', text }]
    };

  } catch (error) {
    console.error(`❌ Tool execution failed: ${error.message}`);
    return {
      content: [{
        type: 'text',
        text: `Error: ${error.message}`
      }],
      isError: true
    };
  }
});

// Start server
const transport = new StdioServerTransport();
await server.connect(transport);
console.error('✅ HuggingFace MCP Gateway started');
