import axios from 'axios';
import { z } from 'zod';
import { logger } from '../lib/logger/Logger';
import { metrics } from '../lib/metrics/Metrics';
import { config } from '../lib/config/Config';

const LocalAIResponseSchema = z.object({
  choices: z.array(z.object({
    message: z.object({
      content: z.string(),
      role: z.literal('assistant')
    })
  }))
});

export class LocalAIOSSProvider {
  private baseURL: string;
  private quotaTracker: Map<string, number> = new Map();
  private circuitBreaker: Map<string, number> = new Map();

  constructor() {
    this.baseURL = config.get().LOCALAI_BASE_URL;
  }

  async callModel(prompt: string, opts: {
    artifactId?: string;
    tenantId?: string;
    model?: string;
  } = {}): Promise<string> {
    const model = opts.model || 'gpt-oss-20b';
    const tenantId = opts.tenantId || 'default';

    // Check quota
    if (!this.checkQuota(tenantId)) {
      throw new Error('Quota exceeded for tenant: ' + tenantId);
    }

    // Check circuit breaker
    if (this.isCircuitOpen(tenantId)) {
      throw new Error('Circuit breaker open for tenant: ' + tenantId);
    }

    const start = process.hrtime.bigint();
    const labels = {
      provider: 'localai-oss',
      tenant: tenantId,
      model
    };

    try {
      const res = await axios.post(
        `${this.baseURL}/v1/chat/completions`,
        {
          model,
          messages: [{ role: 'user', content: prompt }],
          max_tokens: 256,
          temperature: 0.7,
          stream: false
        },
        {
          headers: {
            Authorization: `Bearer ${process.env.LOCALAI_API_KEY || ''}`
          },
          timeout: 30000
        }
      );

      const parsed = LocalAIResponseSchema.parse(res.data);
      const text = parsed.choices[0]?.message.content || '';

      // Update quota
      this.updateQuota(tenantId, text.length);

      // Update metrics
      metrics.httpRequestsTotal.inc({
        ...labels,
        status: 'success'
      });

      const duration = Number((process.hrtime.bigint() - start) / 1_000_000n);
      metrics.httpRequestDuration.observe(labels, duration);

      // Reset circuit breaker on success
      this.resetCircuitBreaker(tenantId);

      return text;
    } catch (e) {
      metrics.counter('localai_oss_requests_total', 'Total LocalAI OSS requests').inc({
        ...labels,
        status: 'error'
      });

      // Trigger circuit breaker
      this.triggerCircuitBreaker(tenantId);

      logger.error('LocalAI OSS call failed', {
        error: e instanceof Error ? e.message : 'Unknown error',
        tenantId,
        model
      });

      throw e;
    }
  }

  private checkQuota(tenantId: string): boolean {
    const quota = config.get().LOCALAI_QUOTA_USD || 20;
    const used = this.quotaTracker.get(tenantId) || 0;
    return used < quota;
  }

  private updateQuota(tenantId: string, tokens: number): void {
    const cost = tokens * 0.002; // $0.002 per token
    const current = this.quotaTracker.get(tenantId) || 0;
    this.quotaTracker.set(tenantId, current + cost);

    metrics.gauge('localai_oss_quota_used', 'LocalAI OSS quota used').set(current + cost, { tenant: tenantId });
  }

  private isCircuitOpen(tenantId: string): boolean {
    const failures = this.circuitBreaker.get(tenantId) || 0;
    return failures >= 3;
  }

  private triggerCircuitBreaker(tenantId: string): void {
    const failures = (this.circuitBreaker.get(tenantId) || 0) + 1;
    this.circuitBreaker.set(tenantId, failures);

    // Auto-reset after 60 seconds
    setTimeout(() => {
      this.resetCircuitBreaker(tenantId);
    }, 60000);
  }

  private resetCircuitBreaker(tenantId: string): void {
    this.circuitBreaker.set(tenantId, 0);
  }

  getQuotaUsage(tenantId: string): number {
    return this.quotaTracker.get(tenantId) || 0;
  }
}

export const localAIOSSProvider = new LocalAIOSSProvider();