
module.exports = {
  // Base URL for the service being benchmarked
  // Can be overridden by CLI arg --base-url
  baseUrl: 'http://localhost:3000',

  // Global thresholds applied to all benchmarks (unless overridden per benchmark)
  // If any threshold is violated, the benchmark run will be marked as failed.
  thresholds: {
    p95Ms: 200, // 95th percentile latency must be < 200ms
    p99Ms: 500, // 99th percentile latency must be < 500ms
    minRps: 10, // Minimum requests per second across all benchmarks
    maxErrorRate: 0.01, // Max 1% error rate
  },

  // Array of benchmark targets
  // Each object defines a specific API endpoint or scenario to test
  benchmarks: [
    {
      id: 'health-check',
      name: 'Health Check Endpoint',
      method: 'GET',
      path: '/health',
      // No specific thresholds for this basic check, global ones apply
    },
    {
      id: 'create-user',
      name: 'Create User API',
      method: 'POST',
      path: '/users',
      body: { name: 'Test User', email: 'test@example.com' },
      headers: { 'X-API-Key': 'some-secret-key' }, // Example custom header
      concurrencyLevels: [10, 50, 100], // Override global concurrency for this benchmark
      thresholds: {
        p95Ms: 300, // This benchmark is slower, allow more latency
      },
    },
    {
      id: 'get-user-data',
      name: 'Get User Data API',
      method: 'GET',
      path: '/users/123',
      // Inherits global thresholds and concurrency logic
    },
  ],

  // Optional: define optimization techniques or scenarios to compare
  // optimizationTechniques: {
  //   'no-cache': { headers: { 'Cache-Control': 'no-cache' } },
  //   'with-cdn': { baseUrl: 'http://cdn.example.com' },
  // },
};
