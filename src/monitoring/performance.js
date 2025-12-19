import os from 'os';
import { metrics } from '@opentelemetry/api';
import { logger } from './logger.js';
import { alertSlowResponse } from './alerts.js';

const meter = metrics.getMeter('performance-monitoring', '1.0.0');

// Performance metrics
const requestDuration = meter.createHistogram('http_request_duration_seconds', {
  description: 'HTTP request duration',
  unit: 's'
});

const databaseQueryDuration = meter.createHistogram('database_query_duration_seconds', {
  description: 'Database query duration',
  unit: 's'
});

const externalApiDuration = meter.createHistogram('external_api_duration_seconds', {
  description: 'External API call duration',
  unit: 's'
});

const memoryUsage = meter.createObservableGauge('process_memory_bytes', {
  description: 'Process memory usage',
  unit: 'bytes'
});

const cpuUsage = meter.createObservableGauge('process_cpu_usage_percent', {
  description: 'Process CPU usage',
  unit: 'percent'
});

/**
 * Performance monitor class
 */
export class PerformanceMonitor {
  constructor(config = {}) {
    this.config = {
      slowRequestThreshold: config.slowRequestThreshold || 1000, // 1 second
      slowQueryThreshold: config.slowQueryThreshold || 500, // 500ms
      slowApiThreshold: config.slowApiThreshold || 2000, // 2 seconds
      ...config
    };

    this.metrics = {
      requests: [],
      queries: [],
      apiCalls: []
    };

    this.maxMetricsSize = 10000;

    // Setup system metrics collection
    this.setupSystemMetrics();
  }

  /**
   * Setup system metrics collection
   */
  setupSystemMetrics() {
    // Memory usage
    memoryUsage.addCallback((observableResult) => {
      const usage = process.memoryUsage();
      observableResult.observe(usage.heapUsed, { type: 'heap_used' });
      observableResult.observe(usage.heapTotal, { type: 'heap_total' });
      observableResult.observe(usage.rss, { type: 'rss' });
      observableResult.observe(usage.external, { type: 'external' });
    });

    // CPU usage
    let lastCpuUsage = process.cpuUsage();
    let lastTime = Date.now();

    cpuUsage.addCallback((observableResult) => {
      const currentCpuUsage = process.cpuUsage(lastCpuUsage);
      const currentTime = Date.now();
      const timeDiff = currentTime - lastTime;

      const userPercent = (currentCpuUsage.user / 1000 / timeDiff) * 100;
      const systemPercent = (currentCpuUsage.system / 1000 / timeDiff) * 100;

      observableResult.observe(userPercent, { type: 'user' });
      observableResult.observe(systemPercent, { type: 'system' });

      lastCpuUsage = process.cpuUsage();
      lastTime = currentTime;
    });
  }

  /**
   * Track HTTP request performance
   */
  trackRequest(req, res, duration) {
    const durationSeconds = duration / 1000;

    requestDuration.record(durationSeconds, {
      method: req.method,
      route: req.route?.path || req.path,
      status: res.statusCode
    });

    const metric = {
      timestamp: new Date().toISOString(),
      method: req.method,
      path: req.path,
      status: res.statusCode,
      duration,
      ip: req.ip
    };

    this.addMetric('requests', metric);

    // Alert on slow requests
    if (duration > this.config.slowRequestThreshold) {
      logger.warn('Slow request detected', metric);
      alertSlowResponse(req.path, duration, this.config.slowRequestThreshold);
    }

    return metric;
  }

  /**
   * Track database query performance
   */
  trackQuery(query, duration, params = {}) {
    const durationSeconds = duration / 1000;

    databaseQueryDuration.record(durationSeconds, {
      query: this.summarizeQuery(query)
    });

    const metric = {
      timestamp: new Date().toISOString(),
      query,
      duration,
      params
    };

    this.addMetric('queries', metric);

    if (duration > this.config.slowQueryThreshold) {
      logger.warn('Slow database query detected', metric);
    }

    return metric;
  }

  /**
   * Track external API call performance
   */
  trackApiCall(service, endpoint, duration, metadata = {}) {
    const durationSeconds = duration / 1000;

    externalApiDuration.record(durationSeconds, {
      service,
      endpoint
    });

    const metric = {
      timestamp: new Date().toISOString(),
      service,
      endpoint,
      duration,
      metadata
    };

    this.addMetric('apiCalls', metric);

    if (duration > this.config.slowApiThreshold) {
      logger.warn('Slow external API call detected', metric);
    }

    return metric;
  }

  /**
   * Add a metric to the history
   */
  addMetric(type, metric) {
    this.metrics[type].unshift(metric);

    if (this.metrics[type].length > this.maxMetricsSize) {
      this.metrics[type] = this.metrics[type].slice(0, this.maxMetricsSize);
    }
  }

  /**
   * Summarize a SQL query
   */
  summarizeQuery(query) {
    return query.trim().split(/\s+/)[0].toUpperCase();
  }

  /**
   * Get performance statistics
   */
  getStats(period = 3600000) { // Default 1 hour
    const since = Date.now() - period;

    const filterByTime = (m) => new Date(m.timestamp).getTime() >= since;

    const recentRequests = this.metrics.requests.filter(filterByTime);
    const recentQueries = this.metrics.queries.filter(filterByTime);
    const recentApiCalls = this.metrics.apiCalls.filter(filterByTime);

    const calculateStats = (arr) => {
      if (arr.length === 0) {
        return { count: 0, avgDuration: 0, p50: 0, p95: 0, p99: 0 };
      }

      const durations = arr.map(m => m.duration).sort((a, b) => a - b);
      const sum = durations.reduce((a, b) => a + b, 0);

      return {
        count: arr.length,
        avgDuration: sum / arr.length,
        p50: durations[Math.floor(arr.length * 0.5)],
        p95: durations[Math.floor(arr.length * 0.95)],
        p99: durations[Math.floor(arr.length * 0.99)]
      };
    };

    return {
      period: `${period / 1000}s`,
      requests: calculateStats(recentRequests),
      queries: calculateStats(recentQueries),
      apiCalls: calculateStats(recentApiCalls)
    };
  }

  /**
   * Get slowest metrics
   */
  getSlowest(type, count = 10) {
    return [...this.metrics[type]]
      .sort((a, b) => b.duration - a.duration)
      .slice(0, count);
  }

  getSlowestRequests(count = 10) { return this.getSlowest('requests', count); }
  getSlowestQueries(count = 10) { return this.getSlowest('queries', count); }
  getSlowestApiCalls(count = 10) { return this.getSlowest('apiCalls', count); }

  /**
   * Get system statistics
   */
  getSystemStats() {
    const mem = process.memoryUsage();
    const uptime = process.uptime();

    return {
      memory: {
        rss: mem.rss,
        heapTotal: mem.heapTotal,
        heapUsed: mem.heapUsed,
        external: mem.external
      },
      cpu: process.cpuUsage(),
      uptime: {
        seconds: uptime,
        formatted: this.formatUptime(uptime)
      },
      loadAvg: os.loadavg()
    };
  }

  /**
   * Format uptime in a readable string
   */
  formatUptime(seconds) {
    const d = Math.floor(seconds / (3600 * 24));
    const h = Math.floor(seconds % (3600 * 24) / 3600);
    const m = Math.floor(seconds % 3600 / 60);

    return `${d}d ${h}h ${m}m`;
  }

  /**
   * Clear all metrics history
   */
  clearMetrics() {
    this.metrics.requests = [];
    this.metrics.queries = [];
    this.metrics.apiCalls = [];
    logger.info('Performance metrics cleared');
  }
}

// Export singleton instance
export const performanceMonitor = new PerformanceMonitor();

// Express middleware for performance tracking
export function performanceMiddleware(req, res, next) {
  const start = Date.now();

  res.on('finish', () => {
    const duration = Date.now() - start;
    performanceMonitor.trackRequest(req, res, duration);
  });

  next();
}
