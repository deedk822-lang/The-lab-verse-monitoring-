/**
 * @jest-environment node
 */
import request from 'supertest';
import app from '../server.js';

describe('Health Check API', () => {
  test('GET /health should return 200 and health status', async () => {
    const response = await request(app).get('/health');

    expect(response.status).toBe(200);
    expect(response.body.status).toBe('healthy');
    expect(response.body).toHaveProperty('timestamp');
    expect(response.body).toHaveProperty('uptime');
    expect(response.body).toHaveProperty('environment');
  });

  test('HEAD /health should return 200', async () => {
    const response = await request(app).head('/health');

    expect(response.status).toBe(200);
  });

  test('GET /api/health should return 200 and health status', async () => {
    const response = await request(app).get('/api/health');

    expect(response.status).toBe(200);
    expect(response.body.status).toBe('healthy');
  });

  test('GET /ready should return 200 ready status', async () => {
    const response = await request(app).get('/ready');

    expect(response.status).toBe(200);
    expect(response.body.status).toBe('ready');
  });

  test('GET /live should return 200 alive status', async () => {
    const response = await request(app).get('/live');

    expect(response.status).toBe(200);
    expect(response.body.status).toBe('alive');
  });
});