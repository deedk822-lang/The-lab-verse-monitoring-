export class MetricsCollector {
  private counters: Record<string, number> = {};

  increment(name: string, value: number = 1): void {
    this.counters[name] = (this.counters[name] || 0) + value;
  }

  counter(name: string): number {
    return this.counters[name] || 0;
  }
}
