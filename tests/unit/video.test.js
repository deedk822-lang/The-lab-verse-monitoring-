const request = require('supertest');
const { createApp } = require('../../src/gateway');

const app = createApp();

describe('POST /api/video/generate', () => {
  it('requires JWT', async () => {
    const res = await request(app).post('/api/video/generate').send({});
    expect(res.statusCode).toBe(401);
  });
});