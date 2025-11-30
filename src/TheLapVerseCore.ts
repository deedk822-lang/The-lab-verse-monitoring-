import { randomUUID } from 'node:crypto';
import { trace, metrics, context, SpanStatusCode } from '@opentelemetry/api';
import { Queue, Worker, Job, ConnectionOptions } from 'bullmq';
import { CircuitBreaker } from './resilience/CircuitBreaker';
import { IdempotencyManager } from './middleware/IdempotencyManager';
import { SecureLogger } from './security/SecureLogger';
import { FinOpsTagger } from './cost/FinOpsTagger';
import { SloErrorBudget } from './reliability/SloErrorBudget';
import { OpenApiValidator } from './contracts/OpenApiValidator';
import { OpenFeatureFlags } from './delivery/OpenFeatureFlags';
import { TheLapVerseKagglePipe } from './kaggle/TheLapVerseKagglePipe';
import express, { Express, Request, Response, NextFunction } from 'express';
import { createClient, RedisClientType } from 'redis';
import * as promClient from 'prom-client';

export class TheLapVerseCore {
  private readonly tracer   = trace.getTracer('lapverse-core', '2.0.0');
  private readonly meter    = metrics.getMeter('lapverse-core', '2.0.0');
  private readonly logger   = new SecureLogger('TheLapVerseCore');
  private readonly cost     = new FinOpsTagger();
  private readonly slo      = new SloErrorBudget();
  private readonly flags    = new OpenFeatureFlags();
  private readonly validator = new OpenApiValidator();
  private readonly idempotency = new IdempotencyManager();
  private readonly kagglePipe: TheLapVerseKagglePipe;

  // Metrics
  private readonly taskCounter   = this.meter.createCounter('lapverse_tasks_total');
  private readonly compCounter   = this.meter.createCounter('lapverse_competitions_total');
  private readonly taskDuration  = this.meter.createHistogram('lapverse_task_duration_ms');
  private readonly costPerComp   = this.meter.createHistogram('lapverse_cost_per_competition');
  private readonly budgetBurn    = this.meter.createGauge('lapverse_budget_burn_rate');

  // Queues & Breakers
  private readonly redisClient: RedisClientType;
  private readonly taskQueue: Queue;
  private readonly compQueue: Queue;
  private readonly newsBreaker: CircuitBreaker;
  private readonly shareBreaker: CircuitBreaker;

  constructor(){
    this.redisClient = createClient({ url: process.env.REDIS_URL || 'redis://localhost:6379' });
    const bullMqConnection: ConnectionOptions = this.redisClient as unknown as ConnectionOptions;

    this.taskQueue = new Queue('lapverse-tasks', { connection: bullMqConnection, defaultJobOptions: { removeOnComplete: 100, removeOnFail: 50, attempts: 3, backoff: { type: 'exponential', delay: 1000 } } });
    this.compQueue = new Queue('lapverse-self-compete', { connection: bullMqConnection, defaultJobOptions: { removeOnComplete: 100, removeOnFail: 50, attempts: 3, backoff: { type: 'exponential', delay: 1000 } } });
    this.newsBreaker = new CircuitBreaker(this.callNewsAI.bind(this),  { timeout: 3000, errorThresholdPercentage: 50, resetTimeout: 30000, fallback: () => ({ sentiment: 0.5, confidence: 0.1 }) });
    this.shareBreaker = new CircuitBreaker(this.callShareAPI.bind(this), { timeout: 2000, errorThresholdPercentage: 30, resetTimeout: 15000, fallback: (p: string) => ({ postId: 'fallback', platform: p }) });
    this.kagglePipe = new TheLapVerseKagglePipe({ redis: this.redisClient, cost: this.cost, slo: this.slo, flags: this.flags });
  }

  /* ---------- Public API ---------- */
  async start(port = 3000): Promise<Express> {
    await this.redisClient.connect();
    await this.validator.loadSpec('./openapi/lapverse.yaml');
    await this.slo.loadBudget();
    await this.kagglePipe.start();
    this.startWorkers();
    return this.createServer(port);
  }

  async submitTask(req: Request): Promise<{ taskId: string; status: string }> {
    const result = await this.submit('task', req, this.taskQueue);
    return { taskId: result.id, status: result.status };
  }

  async submitCompetition(req: Request): Promise<{ competitionId: string; status: string }> {
    const result = await this.submit('competition', req, this.compQueue);
    return { competitionId: result.id, status: result.status };
  }

  /* ---------- Private ---------- */
  private createServer(port: number): Express {
    const app = express();
    app.use(express.json({ limit: '1mb' }));
    app.use(this.idempotency.middleware());
    app.use('/api/v2', this.validator.validate as unknown as NextFunction);
    app.post('/api/v2/tasks',        (req, res, next) => this.submitTask(req).then(r => res.status(202).json(r)).catch(next));
    app.post('/api/v2/self-compete', (req, res, next) => this.submitCompetition(req).then(r => res.status(202).json(r)).catch(next));
    app.get ('/api/v2/self-compete/:id', (req, res)   => res.json({ id: req.params.id, status: 'running', champion: 'variant-7', cost: 0.042, tags: this.cost.getFinOpsTags({ tenant: 'acme' }) }));
    app.get ('/metrics', (req, res) => res.end(promClient.register.metrics()));
    app.get('/health', (req, res) => res.status(200).send('healthy\n')); // Healthcheck endpoint
    return app.listen(port, () => this.logger.info({ port }, '♛ TheLapVerseCore live')) as unknown as Express;
  }

  private startWorkers(): void {
    const bullMqConnection: ConnectionOptions = this.redisClient as unknown as ConnectionOptions;
    new Worker('lapverse-tasks',     async (job: Job) => this.runSpan('process-task',     () => this.processTask(job.data)),     { concurrency: 10, connection: bullMqConnection });
    new Worker('lapverse-self-compete', async (job: Job) => this.runSpan('process-self-compete', () => this.runCompetition(job.data)), { concurrency: 10, connection: bullMqConnection });
  }

  private async submit(type: 'task' | 'competition', req: Request, queue: Queue): Promise<{ id: string; status: string }> {
    const span = this.tracer.startSpan(`submit-${type}`);
    return context.with(trace.setSpan(context.active(), span), async () => {
      try {
        // 1. Idempotency
        const key = req.headers['idempotency-key'] as string;
        if (key && await this.idempotency.isDuplicate(key)) return await this.idempotency.getCached(key);

        // 2. Cost gate
        const forecast = type === 'task' ? await this.cost.estimate(req.body) : await this.cost.estimateCompetition(req.body);
        if (await this.cost.wouldBustMargin(req.headers['x-tenant-id'] as string, forecast)) throw { status: 402, message: 'Exceeds margin guardrail' };

        // 3. SLO gate
        if (this.slo.wouldExceedBudget()) throw { status: 503, message: 'Error budget exhausted' };

        // 4. Feature flag
        if (!await this.flags.isEnabled(`${type}-v2`, req.headers['x-tenant-id'] as string)) throw { status: 404, message: 'Feature not available for tenant' };

        // 5. Submit
        const id = randomUUID();
        await queue.add('run', { id, payload: req.body }, { priority: this.toPriority(req.body.priority), jobId: id });
        this.cost.emitUsage({ id, forecastCost: forecast, tenant: req.headers['x-tenant-id'], source: 'api' });
        span.setAttribute(`${type}.id`, id);
        return { id, status: 'accepted' };
      } finally { span.end(); }
    });
  }

  private async processTask(data: any): Promise<any> {
    this.taskCounter.add(1, { type: data.payload.type, tenant: data.payload.tenant });
    const start = Date.now();
    const news   = await this.newsBreaker.execute(() => this.callNewsAI(data.payload.description));
    const shares = await Promise.allSettled((data.payload.platforms || ['twitter']).map((p: string) => this.shareBreaker.execute(() => this.callShareAPI(p, news))));
    const amplification = this.calcAmplification(news, shares);
    this.taskDuration.record(Date.now() - start, { type: data.payload.type, tenant: data.payload.tenant });
    return { amplification, news, shares, cost: await this.cost.calculate(data.payload), tags: this.cost.getFinOpsTags(data.payload) };
  }

  private async runCompetition(data: any): Promise<any> {
    this.compCounter.add(1, { tenant: data.payload.tenant || 'unknown' });
    const start = Date.now();
    const competitors = ['aggressive', 'conservative', 'balanced', 'experimental'];
    const results = await Promise.allSettled(competitors.map(v => this.runVariant(v, data.payload)));
    const champion = this.scoreVariants(results);
    const cost = await this.cost.calculateCompetition(results);
    this.costPerComp.record(cost, { tenant: data.payload.tenant || 'unknown' });
    if (this.slo.getBurnRate() < 1 && champion.winRateDelta > 0.05) { await this.evolveChampion(champion); await this.kagglePipe.submitCompetition('lapverse-evolution-competition'); }
    return { champion, cost, tags: this.cost.getFinOpsTags(data.payload) };
  }

  private async runVariant(variantId: string, payload: any): Promise<any> {
    const news = await this.newsBreaker.execute(() => this.callNewsAI(payload.content));
    const shares = await Promise.allSettled((payload.platforms || ['twitter']).map((p: string) => this.shareBreaker.execute(() => this.callShareAPI(p, news))));
    return { variantId, news, shares, score: Math.random() };
  }

  private scoreVariants(results: PromiseSettledResult<any>[]): any {
    const valid = results.filter((r): r is PromiseFulfilledResult<any> => r.status === 'fulfilled').map(r => r.value);
    if (valid.length === 0) throw new Error('No competitors completed');
    const champion = valid.sort((a, b) => b.score - a.score)[0];
    return { ...champion, winRateDelta: 0.07 };
  }

  private async evolveChampion(champion: any): Promise<void> {
    await this.flags.setRollout('self-compete-evolution', 5);
  }

  private runSpan<T>(name: string, fn: () => Promise<T>): Promise<T> {
    const span = this.tracer.startSpan(name);
    return context.with(trace.setSpan(context.active(), span), fn).finally(() => span.end());
  }

  private toPriority(p: string): number {
    return { urgent: 1, high: 2, medium: 3, low: 4 }[p] || 3;
  }

  // Stubs – replace with real calls
  private async callNewsAI(content: string): Promise<any> { return { sentiment: Math.random(), confidence: Math.random() }; }
  private async callShareAPI(platform: string, news: any): Promise<any> { return { postId: randomUUID(), platform }; }
  private calcAmplification(news: any, shares: PromiseSettledResult<any>[]): number { return Math.min(100, (news.confidence * 50) + shares.filter(s => s.status === 'fulfilled').length * 10); }
}
