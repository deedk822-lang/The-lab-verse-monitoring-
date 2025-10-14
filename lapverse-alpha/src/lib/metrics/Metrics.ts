import { register, Counter, Histogram, Gauge } from 'prom-client';

export const metrics = {
  // Request metrics
  httpRequestsTotal: new Counter({
    name: 'http_requests_total',
    help: 'Total number of HTTP requests',
    labelNames: ['method', 'route', 'status_code'],
  }),

  httpRequestDuration: new Histogram({
    name: 'http_request_duration_seconds',
    help: 'Duration of HTTP requests',
    labelNames: ['method', 'route'],
    buckets: [0.1, 0.5, 1, 2, 5, 10],
  }),

  // A2A metrics
  a2aTasksCreated: new Counter({
    name: 'a2a_tasks_created_total',
    help: 'Total number of A2A tasks created',
    labelNames: ['category'],
  }),

  a2aRevenueEarned: new Counter({
    name: 'a2a_revenue_earned_total',
    help: 'Total revenue earned from A2A marketplace',
    labelNames: ['type'],
  }),

  // Argilla metrics
  argillaRecordsLogged: new Counter({
    name: 'argilla_records_logged_total',
    help: 'Total number of records logged to Argilla',
    labelNames: ['dataset'],
  }),

  argillaDatasetSales: new Counter({
    name: 'argilla_dataset_sales_total',
    help: 'Total number of dataset sales',
    labelNames: ['pack_id'],
  }),

  // Coliseum metrics
  coliseumBattlesTotal: new Counter({
    name: 'coliseum_battles_total',
    help: 'Total number of Coliseum battles',
  }),

  coliseumBattleDuration: new Histogram({
    name: 'coliseum_battle_duration_seconds',
    help: 'Duration of Coliseum battles',
    buckets: [30, 60, 120, 300, 600],
  }),
};

// Register metrics
register.registerMetric(metrics.httpRequestsTotal);
register.registerMetric(metrics.httpRequestDuration);
register.registerMetric(metrics.a2aTasksCreated);
register.registerMetric(metrics.a2aRevenueEarned);
register.registerMetric(metrics.argillaRecordsLogged);
register.registerMetric(metrics.argillaDatasetSales);
register.registerMetric(metrics.coliseumBattlesTotal);
register.registerMetric(metrics.coliseumBattleDuration);