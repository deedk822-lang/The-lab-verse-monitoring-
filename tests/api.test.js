// tests/api.test.js
import request from 'supertest';
import app from '../server.js';

describe('API Routes', () => {
  test('POST /api/orchestrator should return 400 for invalid request', async () => {
    const response = await request(app)
      .post('/api/orchestrator')
      .send({});

    expect(response.status).toBe(400);
  });

  test('POST /api/models/provision should return 400 for invalid request', async () => {
    const response = await request(app)
      .post('/api/models/provision')
      .send({});

    expect(response.status).toBe(400);
  });

  test('POST /api/hireborderless/budget-allocate should return 400 for invalid request', async () => {
    const response = await request(app)
      .post('/api/hireborderless/budget-allocate')
      .send({});

    expect(response.status).toBe(400);
  });
});
