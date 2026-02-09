import Fastify, { FastifyInstance, FastifyRequest, FastifyReply } from 'fastify';
import { OpenFeature } from '@openfeature/server-sdk';
import { randomUUID } from 'crypto';
import formBodyPlugin from '@fastify/formbody';

// Import the plugins we created
import idempotencyPlugin from './monetization/idempotency';
import metricsPlugin from './otel/metrics';
import featureFlagsPlugin from './features/featureFlags';
import circuitBreakerPlugin from './resilience/circuitBreaker';

const buildServer = (logger = true): FastifyInstance => {
    const server: FastifyInstance = Fastify({ logger });

    // Register all our rival-proof plugins
    server.register(formBodyPlugin);
    server.register(metricsPlugin);
    server.register(idempotencyPlugin);
    server.register(featureFlagsPlugin);
    server.register(circuitBreakerPlugin);

    // Mock a downstream service call that can fail
    async function callMarketData(query: string): Promise<{ data: any; stale: boolean }> {
      // Simulate a 60% failure rate to test the circuit breaker
      if (Math.random() > 0.4) {
        throw new Error('Downstream service is unavailable');
      }
      return { data: { query, prices: [100, 102, 101] }, stale: false };
    }

    // Define the main API route
    server.post('/v1/scout', async (request: FastifyRequest, reply: FastifyReply) => {
      const { query, tenant } = request.body as { query: string; tenant: string };

      // Attach tenant to request for other plugins to use
      request.tenant = tenant;

      // 1. Circuit Breaker + Fallback
      const marketDataBreaker = server.circuitBreaker.create(callMarketData);
      marketDataBreaker.fallback(() => Promise.resolve({ data: { query, prices: [99, 99, 99] }, stale: true }));

      const marketData = await marketDataBreaker.fire(query);

      let price = 0.05; // Base price

      // 2. Feature-flagged pricing
      const featureFlags = server.openfeature;
      const pricingV2Enabled = await featureFlags.getBooleanValue('pricingV2', false, { targetingKey: tenant });

      if (pricingV2Enabled) {
        price = price * 1.20; // 20% uplift experiment
        server.metrics.increment('scout_pricing_v2_exposed', 1, { tenant });
      }

      const response = {
        id: randomUUID(),
        query,
        marketData,
        cost: price,
        tokens: 1 // Simulate token consumption
      };

      // Set response headers as per the blueprint
      reply.header('X-RateLimit-Limit', 1000);
      reply.header('X-RateLimit-Remaining', 999);
      reply.header('X-Scout-Cost-USD', price.toFixed(4));

      // 3. Idempotency and usage metrics are handled by hooks
      return response;
    });

    return server;
}


const start = async () => {
  const server = buildServer();
  try {
    await server.listen({ port: 3000 });
    console.log('✅ Scout Monetization Service is running on port 3000');
  } catch (err) {
    server.log.error(err);
    process.exit(1);
  }
};

if (require.main === module) {
    start();
}

export default buildServer;