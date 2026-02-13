'use strict';

/**
 * Reference config schema expected by monitor.js.
 * Replace endpoints and payloads with your real API routes.
 */

module.exports = {
  baseUrl: process.env.BASE_URL || 'http://localhost:3000',

  thresholds: {
    p95Ms: 200,
    minRps: 1000,
    maxErrorRate: 0.01
  },

  benchmarks: [
    {
      id: 'glm-generation',
      name: 'GLM generation',
      method: 'POST',
      path: '/api/glm/generate',
      body: { prompt: 'hello' }
    },
    {
      id: 'security-analysis',
      name: 'Security analysis',
      method: 'POST',
      path: '/api/security/analyze',
      body: { text: 'sample input' }
    }
  ],

  optimizationTechniques: {
    caching: ['Redis caching', 'HTTP cache headers', 'CDN caching'],
    db: ['Index hot queries', 'Connection pooling', 'Reduce N+1 queries'],
    node: ['Avoid blocking work', 'Stream responses', 'Tune keep-alive'],
    resiliency: ['Circuit breakers', 'Retries with backoff', 'Rate limiting'],
    scaling: ['Horizontal scaling', 'Queue heavy tasks', 'Separate workers']
  }
};
