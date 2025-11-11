import promClient from 'prom-client';

promClient.collectDefaultMetrics();

export const httpReq = new promClient.Histogram({
name: 'ai_provider_request_duration_seconds',
help: 'Latency per AI provider',
labelNames: ['provider', 'model', 'status'],
buckets: [0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10]
});

export const tokenCounter = new promClient.Counter({
name: 'ai_provider_tokens_total',
help: 'Tokens consumed',
labelNames: ['provider', 'model']
});

export const errorCounter = new promClient.Counter({
name: 'ai_provider_errors_total',
help: 'Provider errors',
labelNames: ['provider', 'code']
});
