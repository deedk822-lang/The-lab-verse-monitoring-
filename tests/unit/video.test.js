import request from 'supertest';
import { createApp } from '../../src/gateway.js';

const app = createApp();

describe('POST /api/video/generate', () => {
  it('requires JWT', async () => {
    const res = await request(app).post('/api/video/generate').send({});
    expect(res.statusCode).toBe(401);
  });
});