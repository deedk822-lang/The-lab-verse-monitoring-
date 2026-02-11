import { FastifyInstance, FastifyPluginAsync, FastifyReply, FastifyRequest } from 'fastify';
import { LRU } from 'tiny-lru';
import fp from 'fastify-plugin';

// Augment the FastifyRequest interface to include our custom properties
declare module 'fastify' {
  interface FastifyRequest {
    idempotency?: {
      hash: string;
      cache: LRU<any>;
    };
    tenant?: string;
  }
}

const idempotencyPlugin: FastifyPluginAsync = async (fastify: FastifyInstance) => {
  const cache = new LRU(50_000, 24 * 3600_000); // 24h TTL

  fastify.addHook('preHandler', async (req: FastifyRequest, reply: FastifyReply) => {
    if (!['POST', 'PATCH'].includes(req.method)) {
      return;
    }
    const key = req.headers['idempotency-key'] as string;
    if (!key) {
      throw { statusCode: 400, message: 'Idempotency-Key header is required for POST/PATCH requests' };
    }

    // Create a consistent hash from the key and body
    const hash = key + JSON.stringify(req.body);

    if (cache.has(hash)) {
      const { body, headers } = cache.get(hash);
      reply.headers(headers).send(body);
      return reply; // Stop processing
    }
    // Store the hash and cache instance for use in the onSend hook
    req.idempotency = { hash, cache };
  });

  fastify.addHook('onSend', async (req: FastifyRequest, reply: FastifyReply, payload: any) => {
    // If the request was marked for idempotency, cache the response
    if (req.idempotency) {
      req.idempotency.cache.set(req.idempotency.hash, {
        body: payload,
        headers: reply.getHeaders(),
      });

      // This is where the usage metric would be emitted.
      // We are assuming `fastify.metrics` and `req.tenant` are attached by other plugins.
      if (fastify.metrics && req.tenant) {
        const consumed = JSON.parse(payload)?.tokens || 0;
        fastify.metrics.increment('scout_tokens_consumed', consumed, { tenant: req.tenant });
      }
    }
    return payload;
  });
};

export default fp(idempotencyPlugin, { name: 'idempotency' });