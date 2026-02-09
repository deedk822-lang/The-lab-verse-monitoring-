import { Request, Response } from 'express';
import { MetricsCollector } from '../metrics/MetricsCollector';
import { connectAI } from '../ai/Connector';
import { SloErrorBudget } from '../reliability/SloErrorBudget';
import { FinOpsTagger } from '../cost/FinOpsTagger';

export class HealthChecker {
  private readonly slo: SloErrorBudget;
  private readonly finops: FinOpsTagger;
  private readonly metricsCollector: MetricsCollector;

  constructor(slo: SloErrorBudget, finops: FinOpsTagger, metricsCollector: MetricsCollector) {
    this.slo = slo;
    this.finops = finops;
    this.metricsCollector = metricsCollector;
  }

  async handler(req: Request, res: Response) {
    if (this.slo.wouldExceedBudget()) {
      return res.status(503).json({ status: 'error_budget_exhausted' });
    }

    const metrics = await this.metricsCollector.getMetrics();
    const prompt = `Analyze LapVerse health: ${JSON.stringify(metrics)}. Flag anomalies, suggest evolutions.`;

    try {
      const { qwen, kimi } = await connectAI(prompt, this.finops, {
        artifactId: 'health-check-' + Date.now(),  // Traceable
        tenantId: (req as any).user?.tenantId || 'global'
      });

      res.json({
        status: 'healthy',
        metrics,
        qwen_analysis: qwen,  // Structured health summary
        kimi_evolutions: kimi.evolutions || []  // AI-suggested fixes
      });
    } catch (e: any) {
      console.error('AI Health Check Failed:', e);
      res.status(500).json({ status: 'degraded', error: e.message });
    }
  }
}