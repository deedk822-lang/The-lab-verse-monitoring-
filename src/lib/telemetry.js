import { context, propagation } from '@opentelemetry/api';
import { costTracker } from '../monitoring/costTracking.js';

export const telemetry = {
  traceHeaders(_span) {
    const headers = {};
    propagation.inject(context.active(), headers);
    return headers;
  },
};

export const cost = {
  record({ provider, model, status, duration, inputTokens, stream = false }) {
    const out = Math.round(inputTokens * 0.75);
    costTracker.trackAPICall(provider, model, { inputTokens, outputTokens: out, duration, status, stream });
  },
};
