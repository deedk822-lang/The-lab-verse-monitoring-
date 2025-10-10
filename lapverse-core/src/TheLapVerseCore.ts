import { randomUUID } from 'crypto';
import express from 'express';
import { trace, metrics, context, SpanStatusCode } from '@opentelemetry/api';
import { Queue, Worker } from 'bullmq';
import IORedis from 'ioredis';
import { CircuitBreaker } from './resilience/CircuitBreaker';
import { IdempotencyManager } from './middleware/IdempotencyManager';
import { SecureLogger } from './security/SecureLogger';
import { FinOpsTagger } from './cost/FinOpsTagger';
import { SloErrorBudget } from './reliability/SloErrorBudget';
import { OpenApiValidator } from './contracts/OpenApiValidator';
import { OpenFeatureFlags } from './delivery/OpenFeatureFlags';

export class TheLapVerseCore {
  private tracer   = trace.getTracer('lapverse-core');
  private meter    = metrics.getMeter('lapverse-core');
  private logger   = new SecureLogger();
  private cost     = new FinOpsTagger();
  private slo      = new SloErrorBudget();
  private flags    = new OpenFeatureFlags();
  private validator= new OpenApiValidator();
  private idempotency = new IdempotencyManager();

  // Metrics
  private taskCounter   = this.meter.createCounter('lapverse_tasks_total');
  private taskDuration  = this.meter.createHistogram('lapverse_task_duration_ms');
  private apiCalls      = this.meter.createCounter('lapverse_api_calls_total');
  private errorBudget   = this.meter.createHistogram('lapverse_error_budget_burn');

  // Queues
  private redis = new IORedis(process.env.REDIS_URL || 'redis://localhost:6379');
  private taskQueue  = new Queue('lapverse-tasks', { connection: this.redis });
  private kaggleQ    = new Queue('lapverse-kaggle', { connection: this.redis });

  // Breakers
  private newsBreaker  = new CircuitBreaker(() => this.callNewsAI.bind(this) as any,  { timeout: 3000, errorThreshold: 50, reset: 30000 } as any);
  private shareBreaker = new CircuitBreaker(() => this.callShareAPI.bind(this) as any,{ timeout: 2000, errorThreshold: 30, reset: 15000 } as any);

  async start(port = 3000){
    await this.validator.loadSpec();
    await this.slo.loadBudget?.();
    this.startWorkers();
    return this.createServer(port);
  }

  async submitTask(task: any){
    const span = this.tracer.startSpan('submit-task');
    return context.with(trace.setSpan(context.active(), span), async () => {
      try{
        const key = (task.idempotencyKey as string) || undefined;
        if (key && await this.idempotency.isDuplicate(key)){
          span.setAttribute('idempotency.hit', true as any);
          return await this.idempotency.getCached(key);
        }

        const forecast = await this.cost.estimate(task);
        if (await this.cost.wouldBustMargin(task.tenant, forecast)){
          span.setStatus({ code: SpanStatusCode.ERROR, message: 'Margin guardrail' });
          throw { status: 402, message: 'Task exceeds margin guardrail' };
        }

        if (this.slo.wouldExceedBudget()){
          span.setStatus({ code: SpanStatusCode.ERROR, message: 'Budget exhausted' });
          throw { status: 503, message: 'Error budget exhausted' };
        }

        if (!await this.flags.isEnabled('task-v2', task.tenant)){
          throw { status: 404, message: 'Feature not available for tenant' };
        }

        const job = await this.taskQueue.add('execute', task, { priority: this.toPriority(task.priority) });
        this.cost.emitUsage({ taskId: job.id, forecastCost: forecast, tenant: task.tenant, source: 'api' });
        span.setAttribute('task.id', String(job.id));
        if (task.idempotencyKey) await this.idempotency.setCached(task.idempotencyKey, { taskId: job.id });
        return { taskId: job.id };

      } finally{ span.end(); }
    });
  }

  private createServer(port: number){
    const app = express();
    app.use(express.json());
    app.use(this.idempotency.middleware.bind(this.idempotency));
    app.use('/api', this.validator.validate.bind(this.validator));
    app.post('/api/tasks',  (req,res,next)=>this.submitTask(req.body).then(r=>res.json(r)).catch(next));
    app.get ('/api/status', (_req,res)=>res.json({ slo: this.slo.getBurnRate(), cost: this.cost.getAllocation() }));
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
  }

  private async processTask(task: any){
    this.taskCounter.add(1, { type: task.type, tenant: task.tenant } as any);
    const start = Date.now();

    const news   = await this.newsBreaker.execute(() => this.callNewsAI(task.content));
    const platforms: string[] = (task.platforms||['twitter']);
    const shares = await Promise.allSettled(
      platforms.map(p=>this.shareBreaker.execute(() => this.callShareAPI(p, news)))
    );

    const amplification = this.calcAmplification(news, shares);
    this.taskDuration.record(Date.now() - start, { type: task.type } as any);

    return {
      amplification,
      news,
      shares: shares.map(s=>s.status==='fulfilled'?s.value:{error:(s as any).reason?.message||'share-failed'}),
      cost: await this.cost.calculate(task),
      tags: this.cost.getFinOpsTags(task)
    };
  }

  private async callNewsAI(_content: string){ return { sentiment: 0.9 }; }
  private async callShareAPI(_platform: string, _news: any){ return { postId: randomUUID() }; }
  private calcAmplification(_news: any, _shares: any[]){ return Math.random()*100; }
  private toPriority(p: string){ return ({low:4,medium:3,high:2,urgent:1} as any)[p?.toLowerCase?.()]||3; }
}
