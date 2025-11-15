import { FastifyInstance } from 'fastify';
import client from 'prom-client';
import fp from 'fastify-plugin';

// Augment the FastifyInstance interface to include our custom metrics property
declare module 'fastify' {
  interface FastifyInstance {
    metrics: {
      client: typeof client;
      tokensConsumed: client.Counter;
      pricingV2Exposed: client.Counter;
      increment: (name: string, value: number, labels: Record<string, string>) => void;
    };
  }
}

const metricsPlugin = async (fastify: FastifyInstance) => {
  const register = new client.Registry();
  client.collectDefaultMetrics({ register });

  // Define custom metrics as per the architecture
  const tokensConsumed = new client.Counter({
    name: 'scout_tokens_consumed',
    help: 'Number of tokens consumed by a tenant',
    labelNames: ['tenant'],
    registers: [register],
  });

  const pricingV2Exposed = new client.Counter({
    name: 'scout_pricing_v2_exposed_total',
    help: 'Number of times the v2 pricing feature flag was evaluated for a tenant',
    labelNames: ['tenant'],
    registers: [register],
  });

  // Attach the metrics to the Fastify instance
  fastify.decorate('metrics', {
    client,
    tokensConsumed,
    pricingV2Exposed,
    increment: (name: string, value: number, labels: Record<string, string>) => {
      if (name === 'scout_tokens_consumed') {
        tokensConsumed.inc(labels, value);
      }
      if (name === 'scout_pricing_v2_exposed') {
          pricingV2Exposed.inc(labels, value);
      }
    },
  });

  // Expose the /metrics endpoint
  fastify.get('/metrics', async (request, reply) => {
    reply.header('Content-Type', register.contentType);
    return register.metrics();
  });

  console.log('✅ Prometheus metrics service initialized and /metrics endpoint exposed.');
};

export default fp(metricsPlugin, { name: 'metrics' });