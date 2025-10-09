export class CardinalityWatcher {
  private seriesTracker = new Map<string, number>();
  private readonly MAX_SERIES = 100000;
  private readonly WARNING_THRESHOLD = 0.8;

  async validateMetric(metric: string, labels: Record<string, string>): Promise<boolean> {
    const seriesKey = this.generateSeriesKey(metric, labels);
    const currentCount = this.seriesTracker.get(seriesKey) || 0;

    if (currentCount > this.MAX_SERIES) {
      await this.dropExcessiveSeries(metric, labels);
      return false;
    }

    if (currentCount > (this.MAX_SERIES * this.WARNING_THRESHOLD)) {
      await this.sendCardinalityAlert(metric, currentCount);
    }

    return true;
  }

  private generateSeriesKey(metric: string, labels: Record<string, string>): string {
    const labelStr = Object.entries(labels)
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([k, v]) => `${k}=${v}`)
      .join(',');
    return `${metric}{${labelStr}}`;
  }

  private async dropExcessiveSeries(metric: string, labels: Record<string, string>): Promise<void> {
    console.log(`Dropping metric due to high cardinality: ${metric} with labels ${JSON.stringify(labels)}`);
  }

  private async sendCardinalityAlert(metric: string, count: number): Promise<void> {
    console.log(`High cardinality warning for metric ${metric}: ${count} series`);
  }
}