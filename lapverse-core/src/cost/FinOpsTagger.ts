import { StatsD } from 'hot-shots';

class FinOpsTagger {
  private statsD: StatsD | null = null;

  constructor() {
    if (process.env.STATSD_HOST) {
      this.statsD = new StatsD({
        host: process.env.STATSD_HOST,
        port: 8125,
        prefix: 'finops.'
      });
    }
  }

  estimate(task: any) {
    // This is a placeholder for a more sophisticated estimation logic
    return 1;
  }

  calculate(task: any){ return this.estimate(task); }

  track(service: string, cost: number) {
    if (this.statsD) {
      this.statsD.gauge(service, cost);
    }
  }
}

export { FinOpsTagger };
