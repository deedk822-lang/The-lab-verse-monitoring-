const request = require('supertest');
const { createApp } = require('../../src/gateway');

const app = createApp();

describe('POST /api/text-to-speech', () => {
  it('requires JWT', async () => {
    const res = await request(app).post('/api/text-to-speech').send({});
    expect(res.statusCode).toBe(401);
  });
});