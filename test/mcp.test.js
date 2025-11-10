// test/mcp.test.js
import { jest } from '@jest/globals';
import request from 'supertest';
import express from 'express';
import path from 'path';

// Mock the child_process module
jest.unstable_mockModule('child_process', () => ({
  spawn: jest.fn(),
}));

const { spawn } = await import('child_process');
const mcpHandler = (await import('../api/mcp_server.js')).default;

const app = express();
app.use(express.json());
app.post('/api/mcp', mcpHandler);
app.get('/api/mcp', (req, res) => {
  res.status(405).json({ error: 'Method not allowed' });
});


describe('MCP Server', () => {
  let mockStdout;
  let mockStderr;
  let mockOn;

  beforeEach(() => {
    mockStdout = { on: jest.fn() };
    mockStderr = { on: jest.fn() };
    mockOn = jest.fn((event, callback) => {
      if (event === 'close') {
        callback(0);
      }
    });
    spawn.mockReturnValue({
      stdout: mockStdout,
      stderr: mockStderr,
      on: mockOn,
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('should return a 405 error for GET requests', async () => {
    const res = await request(app).get('/api/mcp');
    expect(res.statusCode).toEqual(405);
    expect(res.body.error).toEqual('Method not allowed');
  });

  it('should call the MCP server with the correct command and args', async () => {
    const mcpPath = path.resolve(process.cwd(), 'node_modules/.bin/mcp-wpcom-remote');
    await request(app)
      .post('/api/mcp')
      .send({ command: 'test', args: ['arg1', 'arg2'] });

    expect(spawn).toHaveBeenCalledWith(mcpPath, [
      'test',
      'arg1',
      'arg2',
    ]);
  });
});
