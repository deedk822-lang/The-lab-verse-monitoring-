import { Counter, Gauge, Histogram, Summary, register } from 'prom-client';

class Metrics {
  counter(name: string, help: string, labelNames?: string[]) {
    return new Counter({ name, help, labelNames, registers: [register] });
  }

  gauge(name: string, help: string, labelNames?: string[]) {
    return new Gauge({ name, help, labelNames, registers: [register] });
  }

  histogram(name: string, help: string, labelNames?: string[], buckets?: number[]) {
    return new Histogram({ name, help, labelNames, buckets, registers: [register] });
  }

  summary(name: string, help: string, labelNames?: string[], percentiles?: number[]) {
    return new Summary({ name, help, labelNames, percentiles, registers: [register] });
  }
}

export const metrics = new Metrics();