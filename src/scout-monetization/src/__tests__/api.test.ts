import { FastifyInstance } from 'fastify';
import { randomUUID } from 'crypto';
import buildServer from '../main';

describe('Scout Monetization API', () => {
  let app: FastifyInstance;

  beforeAll(() => {
    app = buildServer(false); // Disable logger for tests
  });

  afterAll(async () => {
    await app.close();
  });

  test('POST /v1/scout should return success with correct headers', async () => {
    const response = await app.inject({
      method: 'POST',
      url: '/v1/scout',
      headers: {
        'Content-Type': 'application/json',
        'idempotency-key': randomUUID(),
      },
      payload: {
        query: 'test query',
        tenant: 'test-tenant',
      },
    });

    expect(response.statusCode).toBe(200);
    expect(response.headers['x-ratelimit-limit']).toBeDefined();
    expect(response.headers['x-scout-cost-usd']).toBeDefined();
    const body = JSON.parse(response.payload);
    expect(body.query).toBe('test query');
  });

  test('POST /v1/scout without idempotency key should fail', async () => {
    const response = await app.inject({
        method: 'POST',
        url: '/v1/scout',
        headers: {
            'Content-Type': 'application/json',
        },
        payload: {
            query: 'test query',
            tenant: 'test-tenant',
        },
    });

    expect(response.statusCode).toBe(400);
  });
});