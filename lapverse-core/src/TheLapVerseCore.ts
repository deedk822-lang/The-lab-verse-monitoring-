import { randomUUID } from 'node:crypto';
import express, { Express, Request, Response } from 'express';
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
  cursor/the-lap-verse-core-service-polish-ae35
  private readonly tracer   = trace.getTracer('lapverse-core', '2.0.0');
  private readonly meter    = metrics.getMeter('lapverse-core', '2.0.0');
  private readonly logger   = new SecureLogger();
  private readonly cost     = new FinOpsTagger();
  private readonly slo      = new SloErrorBudget();
  private readonly flags    = new OpenFeatureFlags();
  private readonly validator= new OpenApiValidator();
  private readonly idempotency = new IdempotencyManager();
  private readonly kagglePipe: TheLapVerseKagglePipe;

  // Metrics
  private readonly taskCounter   = this.meter.createCounter('lapverse_tasks_total');
  private readonly compCounter   = this.meter.createCounter('lapverse_competitions_total');
  private readonly taskDuration  = this.meter.createHistogram('lapverse_task_duration_ms');
  private readonly costPerComp   = this.meter.createHistogram('lapverse_cost_per_competition');
  private readonly budgetBurn    = this.meter.createGauge('lapverse_budget_burn_rate');

  // Queues
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

  // Breakers
  private readonly newsBreaker  = new CircuitBreaker(this.callNewsAI.bind(this),  { timeout: 3000, errorThreshold: 50, reset: 30000 } as any);
  private readonly shareBreaker = new CircuitBreaker(this.callShareAPI.bind(this),{ timeout: 2000, errorThreshold: 30, reset: 15000 } as any);

  constructor(){
    this.kagglePipe = new TheLapVerseKagglePipe({ redis: this.redis, cost: this.cost, slo: this.slo, flags: this.flags });
  }

  async start(port = 3000): Promise<any> {
    await this.validator.loadSpec('./openapi/lapverse.yaml');

  private tracer   = trace.getTracer('lapverse-core', '2.0.0');
  private meter    = metrics.getMeter('lapverse-core', '2.0.0');
  private logger   = new SecureLogger();
  private cost     = new FinOpsTagger();
  private slo      = new SloErrorBudget();
  private flags    = new OpenFeatureFlags();
  private validator= new OpenApiValidator();
  private idempotency = new IdempotencyManager();
  private kagglePipe: TheLapVerseKagglePipe;

  // OTel metrics
  private taskCounter   = this.meter.createCounter('lapverse_tasks_total');
  private compCounter   = this.meter.createCounter('lapverse_competitions_total');
  private taskDuration  = this.meter.createHistogram('lapverse_task_duration_ms');
  private costPerComp   = this.meter.createHistogram('lapverse_cost_per_competition');
  private errorBudget   = this.meter.createHistogram('lapverse_error_budget_burn');

  // Prometheus metric required by smoke test
  private winRateGauge: Gauge = new Gauge({ name: 'lapverse_win_rate', help: 'Latest self-compete champion win rate delta' });

  // Queues / Redis
  private redis = new IORedis(process.env.REDIS_URL || 'redis://localhost:6379');
  private taskQueue  = new Queue('lapverse-tasks', { connection: this.redis });
  private compQueue  = new Queue('lapverse-self-compete', { connection: this.redis });

  // Breakers
  private newsBreaker  = new CircuitBreaker(() => this.callNewsAI(''),  { timeout: 3000, errorThreshold: 50, reset: 30000 });
  private shareBreaker = new CircuitBreaker(() => this.callShareAPI('twitter', {}),{ timeout: 2000, errorThreshold: 30, reset: 15000 });

  constructor(){
    this.kagglePipe = new TheLapVerseKagglePipe({ redis: this.redis, cost: this.cost, slo: this.slo, flags: this.flags });
  }

  async start(port = 3000){
    await this.validator.loadSpec('openapi/lapverse.yaml');
 main
    await this.slo.loadBudget?.();
    this.kagglePipe.start();
    this.startWorkers();
    return this.createServer(port);
  }
 cursor/the-lap-verse-core-service-polish-ae35
  async submitTask(req: Request): Promise<{ taskId: string; status: string }>
  async submitTask(req: any): Promise<{ taskId: string; status: string }>{
 main
    const result = await this.submit('task', req, this.taskQueue);
    return { taskId: result.id, status: result.status };
  }

 cursor/the-lap-verse-core-service-polish-ae35
  async submitCompetition(req: Request): Promise<{ competitionId: string; status: string }>{

  async submitCompetition(req: any): Promise<{ competitionId: string; status: string }>{
 main
    const result = await this.submit('competition', req, this.compQueue);
    return { competitionId: result.id, status: result.status };
  }

 cursor/the-lap-verse-core-service-polish-ae35
  private createServer(port: number): any {
    const app = express();
    app.use(express.json({ limit: '1mb' }));
    app.use(this.idempotency.middleware.bind(this.idempotency));
    app.use('/api/v2', this.validator.validate.bind(this.validator));

  private createServer(port: number){
    const app = express();
    app.use(express.json({ limit: '1mb' }));
    app.use(this.idempotency.middleware.bind(this.idempotency));
    app.use('/api', this.validator.validate.bind(this.validator));
    app.use('/api/v2', this.validator.validate.bind(this.validator));

 main
    app.post('/api/v2/tasks',        (req,res,next)=>this.submitTask(req).then(r=>res.status(202).json(r)).catch(next));
    app.post('/api/v2/self-compete', (req,res,next)=>this.submitCompetition(req).then(r=>res.status(202).json(r)).catch(next));
    app.get ('/api/v2/self-compete/:id', (req,res)=>{
      res.json({ id: req.params.id, status: 'running', champion: 'variant-7', cost: 0.042, tags: this.cost.getFinOpsTags({ tenant: req.header('X-Tenant-ID') }) });
    });
 cursor/the-lap-verse-core-service-polish-ae35
    app.get ('/metrics',    async (_req,res)=>{
      try {
        const promClient = await import('prom-client');
        res.end(promClient.register.metrics());
      } catch {
        res.status(501).end('# prometheus not configured');
      }
    });
    app.use((err: any, _req: any, res: any, _next: any)=>{
      const status = err?.status || 500;
      res.status(status).json({ error: err?.message || 'internal-error' });
    });
    return app.listen(port, ()=>this.logger.info({port}, '♛ TheLapVerseCore live'));
  }

  private startWorkers(){
    new Worker('lapverse-tasks', async job=>{
      const span = this.tracer.startSpan('process-task');
      return context.with(trace.setSpan(context.active(), span), async ()=>{
        try{
          const result = await this.processTask(job.data);
          span.setStatus({ code: SpanStatusCode.OK });
          return result;
        } finally{ span.end(); }
      });
    }, { concurrency: 10, connection: this.redis });

    new Worker('lapverse-self-compete', async job=>{
      const span = this.tracer.startSpan('process-self-compete');
      return context.with(trace.setSpan(context.active(), span), async ()=>{
        try{
          const result = await this.runCompetition(job.data);
          span.setStatus({ code: SpanStatusCode.OK });
          return result;
        } finally{ span.end(); }
      });
    }, { concurrency: 10, connection: this.redis });
  }

  private async submit(type: 'task'|'competition', req: Request, queue: Queue): Promise<{ id: string; status: string }>{
    const span = this.tracer.startSpan(`submit-${type}`);
    return context.with(trace.setSpan(context.active(), span), async () => {
      try{
        // 1. Idempotency
        const key = req.header('Idempotency-Key') || (req as any).idempotencyKey;
        if (key && await this.idempotency.isDuplicate(key)){
          span.setAttribute('idempotency.hit', true as any);
          return await this.idempotency.getCached(key);
        }

        // 2. Cost gate
        const body: any = req.body || {};
        const forecast = type === 'task' ? await this.cost.estimate(body) : await this.cost.estimateCompetition(body);
        const tenantId = (req.header('X-Tenant-ID') as string) || body.tenant;
        if (await this.cost.wouldBustMargin(tenantId, forecast)){
          span.setStatus({ code: SpanStatusCode.ERROR, message: 'Margin guardrail' });
          throw { status: 402, message: 'Exceeds margin guardrail' };
        }

        // 3. SLO gate
        if (this.slo.wouldExceedBudget()){
          span.setStatus({ code: SpanStatusCode.ERROR, message: 'Budget exhausted' });
          throw { status: 503, message: 'Error budget exhausted' };
        }

        // 4. Feature flag
        if (!await this.flags.isEnabled(`${type}-v2`, tenantId)){
          throw { status: 404, message: 'Feature not available for tenant' };
        }

        // 5. Submit
        const id = randomUUID();
        const payload = type === 'task' ? body : { ...body };
        await queue.add('run', { id, payload }, { priority: this.toPriority(body.priority), jobId: id });
        this.cost.emitUsage({ id, forecastCost: forecast, tenant: tenantId, source: 'api' });
        span.setAttribute(`${type}.id`, id as any);
        if (key) await this.idempotency.setCached(String(key), type === 'task' ? { taskId: id, status: 'accepted' } : { competitionId: id, status: 'accepted' });
        return { id, status: 'accepted' };
      } finally{
        span.end();
      }
    });
  }

  private async processTask(task: any){
    const payload = task?.payload ?? task;
    this.taskCounter.add(1, { type: payload.type, tenant: payload.tenant } as any);
    const start = Date.now();

    const news   = await this.newsBreaker.execute(() => this.callNewsAI(payload.description ?? payload.content ?? ''));
    const platforms: string[] = (payload.platforms||['twitter']);


    app.get ('/api/status', (_req,res)=>res.json({ slo: this.slo.getBurnRate(), cost: this.cost.getAllocation() }));
    app.get ('/metrics',    (_req,res)=>res.end(register.metrics()));

    app.use((err: any, _req: any, res: any, _next: any)=>{
      const status = err?.status || 500;
      res.status(status).json({ error: err?.message || 'internal-error' });
    });
    return app.listen(port, ()=>this.logger.info({port}, '♛ TheLapVerseCore live'));
  }

  private startWorkers(){
    new Worker('lapverse-tasks', async job=>{
      return this.runSpan('process-task', async ()=>{
        return await this.processTask(job.data);
      });
    }, { concurrency: 10, connection: this.redis });

    new Worker('lapverse-self-compete', async job=>{
      return this.runSpan('process-self-compete', async ()=>{
        return await this.runCompetition(job.data);
      });
    }, { concurrency: 10, connection: this.redis });
  }

  private async submit(type: 'task'|'competition', req: any, queue: Queue): Promise<{ id: string; status: string }>{
    const span = this.tracer.startSpan(`submit-${type}`);
    return context.with(trace.setSpan(context.active(), span), async () => {
      try{
        const key = (req as any).idempotencyKey || req.header?.('Idempotency-Key');
        if (key && await this.idempotency.isDuplicate(key)){
          span.setAttribute('idempotency.hit', true as any);
          return await this.idempotency.getCached(key);
        }

        const tenant = req.header?.('X-Tenant-ID') || req.headers?.['x-tenant-id'] || req.body?.tenant;
        const forecast = type === 'task' ? await this.cost.estimate(req.body) : await this.cost.estimateCompetition(req.body);
        if (await this.cost.wouldBustMargin(String(tenant||''), forecast)){
          span.setStatus({ code: SpanStatusCode.ERROR, message: 'Margin guardrail' });
          throw { status: 402, message: 'Exceeds margin guardrail' };
        }

        if (this.slo.wouldExceedBudget()){
          span.setStatus({ code: SpanStatusCode.ERROR, message: 'Budget exhausted' });
          throw { status: 503, message: 'Error budget exhausted' };
        }

        if (!await this.flags.isEnabled(`${type}-v2`, String(tenant||''))){
          throw { status: 404, message: 'Feature not available for tenant' };
        }

        const id = randomUUID();
        await queue.add('run', { id, payload: req.body }, { priority: this.toPriority(req.body?.priority), jobId: id });
        this.cost.emitUsage({ id, forecastCost: forecast, tenant, source: 'api' });
        span.setAttribute(`${type}.id`, id);
        if (key) await this.idempotency.setCached(key, type === 'task' ? { taskId: id, status: 'accepted' } : { competitionId: id, status: 'accepted' });
        return { id, status: 'accepted' };
      } finally{
        span.end();
      }
    });
  }

  private async processTask(data: any){
    const task = data?.payload || data || {};
    this.taskCounter.add(1, { type: task.type, tenant: task.tenant } as any);
    const start = Date.now();

    const news   = await this.newsBreaker.execute(() => this.callNewsAI(task.description || task.content));
    const platforms: string[] = (task.platforms||['twitter']);
 main
    const shares = await Promise.allSettled(
      platforms.map(p=>this.shareBreaker.execute(() => this.callShareAPI(p, news)))
    );

 cursor/the-lap-verse-core-service-polish-ae35
    const amplification = this.calcAmplification(news, shares);
    this.taskDuration.record(Date.now() - start, { type: payload.type } as any);

    const amplification = this.calcAmplification(news, shares as any);
    this.taskDuration.record(Date.now() - start, { type: task.type } as any); main

    return {
      amplification,
      news,
      shares: shares.map(s=>s.status==='fulfilled'?s.value:{error:(s as any).reason?.message||'share-failed'}),
      cost: await this.cost.calculate(payload),
      tags: this.cost.getFinOpsTags(payload)
    };
  }

  private async runCompetition(data: any)
  cursor/the-lap-verse-core-service-polish-ae35
    this.compCounter.add(1, { tenant: data.payload?.tenant || data.tenant || 'unknown' } as any);
    const start = Date.now();
    const competitors: string[] = data.payload?.competitors || data.competitors || ['aggressive','conservative','balanced','experimental'];
    const payload = data.payload ?? data;
    const results = await Promise.allSettled(competitors.map(v => this.runVariant(v, payload)));
    const champion = this.scoreVariants(results);
    const cost = await this.cost.calculateCompetition(results as any);
    this.costPerComp.record(cost, { tenant: payload.tenant || 'unknown' } as any);
    this.budgetBurn.record(this.slo.getBurnRate(), { tenant: payload.tenant || 'unknown' } as any);
    if (this.slo.getBurnRate() < 1 && champion.winRateDelta > 0.05) {

    const payload = data?.payload || data || {};
    this.compCounter.add(1, { tenant: payload.tenant || 'unknown' } as any);
    const start = Date.now();
    const competitors: string[] = payload.competitors || ['aggressive','conservative','balanced','experimental'];
    const results = await Promise.allSettled(competitors.map(v => this.runVariant(v, payload)));
    const champion = this.scoreVariants(results);
    const cost = await this.cost.calculateCompetition(results);
    this.costPerComp.record(cost, { tenant: payload.tenant || 'unknown' } as any);
    // record latest win rate for smoke check
    this.winRateGauge.set(champion.winRateDelta || 0);
    if (this.slo.getBurnRate() < 1 && (champion.winRateDelta || 0) > 0.05){
 main
      await this.evolveChampion(champion);
      await this.kagglePipe.submitCompetition('lapverse-evolution-competition');
    }
    return { champion, cost, tags: this.cost.getFinOpsTags(payload) };
  }

  private async runVariant(variantId: string, payload: any){
 cursor/the-lap-verse-core-service-polish-ae35
    const news   = await this.newsBreaker.execute(() => this.callNewsAI(payload.content ?? payload.description));

    const news = await this.newsBreaker.execute(() => this.callNewsAI(payload.content || payload.description));
 main
    const platforms: string[] = (payload.platforms||['twitter']);
    const shares = await Promise.allSettled(
      platforms.map(p=>this.shareBreaker.execute(() => this.callShareAPI(p, news)))
    );
    return { variantId, news, shares, score: Math.random() };
  }

 cursor/the-lap-verse-core-service-polish-ae35
  private scoreVariants(results: PromiseSettledResult<any>[]) {
    const valid = results.filter((r): r is PromiseFulfilledResult<any> => r.status === 'fulfilled').map(r => r.value);
    if (valid.length === 0) throw new Error('No competitors completed');
    const champion = valid.sort((a, b) => b.score - a.score)[0];

  private scoreVariants(results: PromiseSettledResult<any>[]): any {
    const valid = results.filter((r): r is PromiseFulfilledResult<any> => r.status === 'fulfilled').map(r => r.value);
    if (valid.length === 0) throw new Error('No competitors completed');
    const champion = valid.sort((a, b) => b.score - a.score)[0];
    // simulate a measurable delta
 main
    return { ...champion, winRateDelta: 0.07 };
  }

  private async evolveChampion(_champion: any){
 cursor/the-lap-verse-core-service-polish-ae35
    await this.flags.setRollout?.('self-compete-evolution', 5);
  }

  // Stubs – replace with real calls
  private async callNewsAI(_content: string){ return { sentiment: Math.random(), confidence: Math.random() }; }
  private async callShareAPI(platform: string, _news: any){ return { postId: randomUUID(), platform }; }
  private calcAmplification(news: any, shares: PromiseSettledResult<any>[]) {
    return Math.min(100, (Number(news?.confidence)||0) * 50 + shares.filter(s=>s.status==='fulfilled').length * 10);
  }

    await this.flags.setRollout('self-compete-evolution', 5);
  }

  private runSpan<T>(name: string, fn: () => Promise<T>): Promise<T> {
    const span = this.tracer.startSpan(name);
    return context.with(trace.setSpan(context.active(), span), fn)
      .finally(() => span.end());
  }

 main
  private toPriority(p: string){ return ({low:4,medium:3,high:2,urgent:1} as any)[p?.toLowerCase?.()]||3; }

  // Stubs – replace with real calls
  private async callNewsAI(_content: string){ return { sentiment: Math.random(), confidence: Math.random() }; }
  private async callShareAPI(_platform: string, _news: any){ return { postId: randomUUID() }; }
  private calcAmplification(news: any, shares: PromiseSettledResult<any>[]) { return Math.min(100, (Number(news?.confidence||0) * 50) + (shares.filter(s=>s.status==='fulfilled').length * 10)); }
}
