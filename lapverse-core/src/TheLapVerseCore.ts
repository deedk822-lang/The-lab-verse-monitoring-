import { randomUUID } from 'node:crypto';
import express from 'express';
import { trace, metrics, context, SpanStatusCode } from '@opentelemetry/api';
import { Queue, Worker } from 'bullmq';
import IORedis from 'ioredis';
import { Gauge, register } from 'prom-client';
import { CircuitBreaker } from './resilience/CircuitBreaker';
import { IdempotencyManager } from './middleware/IdempotencyManager';
import { SecureLogger } from './security/SecureLogger';
import { FinOpsTagger } from './cost/FinOpsTagger';
import { SloErrorBudget } from './reliability/SloErrorBudget';
import { OpenApiValidator } from './contracts/OpenApiValidator';
import { OpenFeatureFlags } from './delivery/OpenFeatureFlags';
import { TheLapVerseKagglePipe } from './kaggle/TheLapVerseKagglePipe';

export class TheLapVerseCore {
  private readonly tracer   = trace.getTracer('lapverse-core', '2.0.0');
  private readonly meter    = metrics.getMeter('lapverse-core', '2.0.0');
  private readonly logger   = new SecureLogger();
  private readonly cost     = new FinOpsTagger();
  private readonly slo      = new SloErrorBudget();
  private readonly flags    = new OpenFeatureFlags();
  private readonly validator= new OpenApiValidator();
  private readonly idempotency = new IdempotencyManager();
  private readonly kagglePipe: TheLapVerseKagglePipe;

  private readonly taskCounter   = this.meter.createCounter('lapverse_tasks_total');
  private readonly compCounter   = this.meter.createCounter('lapverse_competitions_total');
  private readonly taskDuration  = this.meter.createHistogram('lapverse_task_duration_ms');
  private readonly costPerComp   = this.meter.createHistogram('lapverse_cost_per_competition');
  private readonly budgetBurn    = this.meter.createGauge('lapverse_budget_burn_rate');

  private readonly winRateGauge: Gauge = new Gauge({
    name: 'lapverse_win_rate',
    help: 'Latest self-compete champion win rate delta'
  });

  private readonly redis = new IORedis(process.env.REDIS_URL || 'redis://localhost:6379');
  private readonly taskQueue  = new Queue('lapverse-tasks', {
    connection: this.redis,
    defaultJobOptions: {
      removeOnComplete: 100,
      removeOnFail: 50,
      attempts: 3,
      backoff: { type: 'exponential', delay: 1000 }
    }
  });
  private readonly compQueue  = new Queue('lapverse-self-compete', {
    connection: this.redis,
    defaultJobOptions: {
      removeOnComplete: 100,
      removeOnFail: 50,
      attempts: 3,
      backoff: { type: 'exponential', delay: 1000 }
    }
  });

  private readonly newsBreaker  = new CircuitBreaker(
    this.callNewsAI.bind(this),
    { timeout: 3000, errorThreshold: 50, reset: 30000 }
  );
  private readonly shareBreaker = new CircuitBreaker(
    this.callShareAPI.bind(this),
    { timeout: 2000, errorThreshold: 30, reset: 15000 }
  );

  constructor(){
    this.kagglePipe = new TheLapVerseKagglePipe({
      redis: this.redis,
      cost: this.cost,
      slo: this.slo,
      flags: this.flags
    });
  }

  async start(port = 3000): Promise<void> {
    await this.validator.loadSpec('openapi/lapverse.yaml');
    await this.slo.loadBudget?.();
    this.kagglePipe.start();
    this.startWorkers();
    this.createServer(port);
  }

  async submitTask(req: any): Promise<{ taskId: string; status: string }> {
    const result = await this.submit('task', req, this.taskQueue);
    return { taskId: result.id, status: result.status };
  }

  async submitCompetition(req: any): Promise<{ competitionId: string; status: string }> {
    const result = await this.submit('competition', req, this.compQueue);
    return { competitionId: result.id, status: result.status };
  }

  private createServer(port: number): void {
    const app = express();
    app.use(express.json({ limit: '1mb' }));
    app.use(this.idempotency.middleware.bind(this.idempotency));
    app.use('/api/v2', this.validator.validate.bind(this.validator));

    app.post('/api/v2/tasks', (req, res, next) =>
      this.submitTask(req).then(r => res.status(202).json(r)).catch(next)
    );

    app.post('/api/v2/self-compete', (req, res, next) =>
      this.submitCompetition(req).then(r => res.status(202).json(r)).catch(next)
    );

    app.get('/api/v2/self-compete/:id', (req, res) => {
      res.json({
        id: req.params.id,
        status: 'running',
        champion: 'variant-7',
        cost: 0.042,
        tags: this.cost.getFinOpsTags({ tenant: req.header('X-Tenant-ID') })
      });
    });

    app.get('/api/status', (_req, res) =>
      res.json({
        slo: this.slo.getBurnRate(),
        cost: this.cost.getAllocation()
      })
    );

    app.get('/metrics', (_req, res) => res.end(register.metrics()));

    app.use((err: any, _req: any, res: any, _next: any) => {
      const status = err?.status || 500;
      res.status(status).json({ error: err?.message || 'internal-error' });
    });

    app.listen(port, () => this.logger.info({ port }, '♛ TheLapVerseCore live'));
  }

  private startWorkers(): void {
    new Worker('lapverse-tasks', async job => {
      return this.runSpan('process-task', async (span) => {
        span.setAttributes({
          'artifact.id': job.data.id,
          'artifact.tenant_id': job.data.tenant,
          'artifact.type': 'task'
        });
        return await this.processTask(job.data);
      });
    }, { concurrency: 10, connection: this.redis });

    new Worker('lapverse-self-compete', async job => {
      return this.runSpan('process-self-compete', async (span) => {
        span.setAttributes({
          'artifact.id': job.data.id,
          'artifact.tenant_id': job.data.tenant,
          'artifact.type': 'competition'
        });
        return await this.runCompetition(job.data);
      });
    }, { concurrency: 10, connection: this.redis });
  }

  private async submit(
    type: 'task' | 'competition',
    req: any,
    queue: Queue
  ): Promise<{ id: string; status: string }> {
    const span = this.tracer.startSpan(`submit-${type}`);
    const id = randomUUID();
    const tenant = req.header?.('X-Tenant-ID') || req.headers?.['x-tenant-id'] || req.body?.tenant || 'anonymous';

    span.setAttributes({
      'artifact.id': id,
      'artifact.tenant_id': tenant,
      'artifact.evolution_depth': 0, // Initial submission
      'artifact.type': type,
      'finops.cost_center': req.body?.cost_center || 'project-default',
      'gen_ai.request.model': 'deepseek-r1' // Default model
    });

    return context.with(trace.setSpan(context.active(), span), async () => {
      try {
        const key = (req as any).idempotencyKey || req.header?.('Idempotency-Key');
        if (key && await this.idempotency.isDuplicate(key)) {
          span.setAttribute('idempotency.hit', true);
          return await this.idempotency.getCached(key);
        }

        const forecast = type === 'task'
          ? await this.cost.estimate(req.body)
          : await this.cost.estimateCompetition(req.body);

        if (await this.cost.wouldBustMargin(tenant, forecast)) {
          span.setStatus({ code: SpanStatusCode.ERROR, message: 'Margin guardrail' });
          throw { status: 402, message: 'Exceeds margin guardrail' };
        }

        if (this.slo.wouldExceedBudget()) {
          span.setStatus({ code: SpanStatusCode.ERROR, message: 'Budget exhausted' });
          throw { status: 503, message: 'Error budget exhausted' };
        }

        if (!await this.flags.isEnabled(`${type}-v2`, tenant)) {
          throw { status: 404, message: 'Feature not available for tenant' };
        }

        await queue.add('run', { id, payload: req.body, tenant }, {
          priority: this.toPriority(req.body?.priority),
          jobId: id
        });

        this.cost.emitUsage({ id, forecastCost: forecast, tenant, source: 'api' });

        if (key) {
          await this.idempotency.setCached(
            key,
            type === 'task'
              ? { taskId: id, status: 'accepted' }
              : { competitionId: id, status: 'accepted' }
          );
        }

        return { id, status: 'accepted' };
      } finally {
        span.end();
      }
    });
  }

  private async processTask(data: any): Promise<any> {
    const { id, payload, tenant } = data;
    const task = payload || {};
    this.taskCounter.add(1, { type: task.type, tenant: tenant } as any);
    const start = Date.now();

    const news = await this.newsBreaker.execute(() =>
      this.callNewsAI(task.description || task.content, id, tenant)
    );

    const platforms: string[] = (task.platforms || ['twitter']);
    const shares = await Promise.allSettled(
      platforms.map(p => this.shareBreaker.execute(() => this.callShareAPI(p, news)))
    );

    const amplification = this.calcAmplification(news, shares);
    this.taskDuration.record(Date.now() - start, { type: task.type } as any);

    return {
      amplification,
      news,
      shares: shares.map(s =>
        s.status === 'fulfilled'
          ? s.value
          : { error: (s as any).reason?.message || 'share-failed' }
      ),
      cost: await this.cost.calculate(task),
      tags: this.cost.getFinOpsTags(task)
    };
  }

  private async runCompetition(data: any): Promise<any> {
    const { id, payload, tenant } = data;
    this.compCounter.add(1, { tenant: tenant || 'unknown' } as any);
    const start = Date.now();

    const competitors: string[] = payload.competitors || [
      'aggressive', 'conservative', 'balanced', 'experimental'
    ];

    const results = await Promise.allSettled(
      competitors.map((v, i) => this.runVariant(v, payload, `${id}-v${i}`, tenant))
    );

    const champion = this.scoreVariants(results);
    const cost = await this.cost.calculateCompetition(results);
    this.costPerComp.record(cost, { tenant: tenant || 'unknown' } as any);
    this.budgetBurn.record(this.slo.getBurnRate(), { tenant: tenant || 'unknown' } as any);
    this.winRateGauge.set(champion.winRateDelta || 0);

    if (this.slo.getBurnRate() < 1 && (champion.winRateDelta || 0) > 0.05) {
      await this.evolveChampion(champion);
      await this.kagglePipe.submitCompetition('lapverse-evolution-competition');
    }

    return {
      champion,
      cost,
      tags: this.cost.getFinOpsTags(payload)
    };
  }

  private async runVariant(variantId: string, payload: any, artifactId: string, tenant: string): Promise<any> {
    return this.runSpan(`run-variant:${variantId}`, async (span) => {
      span.setAttributes({
        'artifact.id': artifactId,
        'artifact.tenant_id': tenant,
        'artifact.type': 'variant',
        'artifact.evolution_depth': (payload.evolution_depth || 0) + 1,
      });

      const news = await this.newsBreaker.execute(() =>
        this.callNewsAI(payload.content || payload.description, artifactId, tenant)
      );

      const platforms: string[] = (payload.platforms || ['twitter']);
      const shares = await Promise.allSettled(
        platforms.map(p => this.shareBreaker.execute(() => this.callShareAPI(p, news)))
      );

      return { variantId, news, shares, score: Math.random() };
    });
  }

  private scoreVariants(results: PromiseSettledResult<any>[]): any {
    const valid = results
      .filter((r): r is PromiseFulfilledResult<any> => r.status === 'fulfilled')
      .map(r => r.value);

    if (valid.length === 0) throw new Error('No competitors completed');

    const champion = valid.sort((a, b) => b.score - a.score)[0];
    return { ...champion, winRateDelta: 0.07 };
  }

  private async evolveChampion(_champion: any): Promise<void> {
    await this.flags.setRollout('self-compete-evolution', 5);
  }

  private runSpan<T>(name: string, fn: (span: import('@opentelemetry/api').Span) => Promise<T>): Promise<T> {
    const span = this.tracer.startSpan(name);
.
    return context.with(trace.setSpan(context.active(), span), () => fn(span))
      .finally(() => span.end());
  }

  private toPriority(p: string): number {
    return ({ low: 4, medium: 3, high: 2, urgent: 1 } as any)[p?.toLowerCase?.()] || 3;
  }

  private async callNewsAI(content: string, artifactId: string, tenant: string): Promise<any> {
    return this.runSpan('call-news-ai', async (span) => {
      span.setAttributes({
        'gen_ai.request.model': 'deepseek-r1',
        'artifact.id': artifactId,
        'artifact.tenant_id': tenant,
      });
      // Simulate LLM call
      const promptTokens = content.length;
      const completionTokens = Math.floor(Math.random() * 200) + 50;
      const model = 'deepseek-r1';

      this.cost.trackLlmUsage(promptTokens + completionTokens, {
        artifact_id: artifactId,
        tenant: tenant,
        model: model,
        operation: 'remix' // Or classify based on context
      });

      span.setAttributes({
        'llm.token_count.prompt': promptTokens,
        'llm.token_count.completion': completionTokens,
      });

      // Mocked response
      return { sentiment: Math.random(), confidence: Math.random(), tokensUsed: promptTokens + completionTokens };
    });
  }

  private async callShareAPI(platform: string, _news: any): Promise<any> {
    return { postId: randomUUID(), platform };
  }

  private calcAmplification(news: any, shares: PromiseSettledResult<any>[]): number {
    return Math.min(
      100,
      (Number(news?.confidence || 0) * 50) +
      (shares.filter(s => s.status === 'fulfilled').length * 10)
    );
  }
}