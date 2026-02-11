import express from 'express';
import { logger } from '../monitoring/logger.js';
import { performanceMonitor } from '../monitoring/performance.js';
import { alertManager } from '../monitoring/alerts.js';
import { costTracker } from '../monitoring/costTracking.js';
import { syntheticMonitor } from '../monitoring/synthetic.js';

const router = express.Router();

/**
 * GET /api/monitoring/overview
 * Get overall monitoring overview
 */
router.get('/overview', (req, res) => {
  try {
    const overview = {
      timestamp: new Date().toISOString(),
      performance: performanceMonitor.getStats(),
      alerts: alertManager.getStats(),
      costs: {
        total: costTracker.getTotalCost(),
        byService: costTracker.getCostByService(),
        alerts: costTracker.checkAlerts(),
      },
      synthetic: syntheticMonitor.getStatus(),
      system: performanceMonitor.getSystemStats(),
    };

    res.json(overview);
  } catch (error) {
    logger.error('Failed to get monitoring overview', { error: error.message });
    res.status(500).json({ error: 'Failed to fetch monitoring data' });
  }
});

/**
 * GET /api/monitoring/performance
 * Get detailed performance metrics
 */
router.get('/performance', (req, res) => {
  try {
    const period = parseInt(req.query.period) || 3600000; // Default 1 hour

    const performance = {
      stats: performanceMonitor.getStats(period),
      slowest: {
        requests: performanceMonitor.getSlowestRequests(10),
        queries: performanceMonitor.getSlowestQueries(10),
        apiCalls: performanceMonitor.getSlowestApiCalls(10),
      },
    };

    res.json(performance);
  } catch (error) {
    logger.error('Failed to get performance metrics', { error: error.message });
    res.status(500).json({ error: 'Failed to fetch performance data' });
  }
});

/**
 * GET /api/monitoring/alerts
 * Get alert history and statistics
 */
router.get('/alerts', (req, res) => {
  try {
    const { severity, since, limit } = req.query;

    const filters = {
      severity,
      since,
      limit: parseInt(limit) || 100,
    };

    const alerts = {
      history: alertManager.getHistory(filters),
      stats: alertManager.getStats(),
    };

    res.json(alerts);
  } catch (error) {
    logger.error('Failed to get alerts', { error: error.message });
    res.status(500).json({ error: 'Failed to fetch alerts' });
  }
});

/**
 * POST /api/monitoring/alerts/test
 * Send a test alert
 */
router.post('/alerts/test', async (req, res) => {
  try {
    const { title, message, severity, channels } = req.body;

    const alert = await alertManager.sendAlert({
      title: title || 'Test Alert',
      message: message || 'This is a test alert from the monitoring system',
      severity: severity || 'low',
      channels: channels || ['log'],
      metadata: { test: true },
    });

    res.json({ success: true, alert });
  } catch (error) {
    logger.error('Failed to send test alert', { error: error.message });
    res.status(500).json({ error: 'Failed to send test alert' });
  }
});

/**
 * GET /api/monitoring/costs
 * Get cost tracking data
 */
router.get('/costs', (req, res) => {
  try {
    const period = req.query.period || 'day';

    const costs = {
      total: costTracker.getTotalCost(),
      byService: costTracker.getCostByService(),
      byPeriod: costTracker.getCostByPeriod(period),
      metrics: costTracker.getMetrics(),
      alerts: costTracker.checkAlerts(),
      projections: {
        daily: costTracker.projectDailyCost(),
        monthly: costTracker.projectMonthlyCost(),
      },
    };

    res.json(costs);
  } catch (error) {
    logger.error('Failed to get cost data', { error: error.message });
    res.status(500).json({ error: 'Failed to fetch cost data' });
  }
});

/**
 * POST /api/monitoring/costs/reset
 * Reset cost tracking (admin only)
 */
router.post('/costs/reset', (req, res) => {
  try {
    // Add authentication check here
    costTracker.resetCosts();

    logger.info('Cost tracking reset by admin');
    res.json({ success: true, message: 'Cost tracking reset' });
  } catch (error) {
    logger.error('Failed to reset costs', { error: error.message });
    res.status(500).json({ error: 'Failed to reset costs' });
  }
});

/**
 * GET /api/monitoring/synthetic
 * Get synthetic monitoring status
 */
router.get('/synthetic', (req, res) => {
  try {
    const status = syntheticMonitor.getStatus();

    const synthetic = {
      status,
      endpoints: Object.entries(status).map(([name, data]) => ({
        name,
        ...data,
        uptime: syntheticMonitor.getUptimePercentage(name),
      })),
    };

    res.json(synthetic);
  } catch (error) {
    logger.error('Failed to get synthetic monitoring data', { error: error.message });
    res.status(500).json({ error: 'Failed to fetch synthetic monitoring data' });
  }
});

/**
 * POST /api/monitoring/synthetic/check
 * Trigger manual synthetic check
 */
router.post('/synthetic/check', async (req, res) => {
  try {
    await syntheticMonitor.runChecks();
    const status = syntheticMonitor.getStatus();

    res.json({ success: true, status });
  } catch (error) {
    logger.error('Failed to run synthetic check', { error: error.message });
    res.status(500).json({ error: 'Failed to run synthetic check' });
  }
});

/**
 * GET /api/monitoring/logs
 * Get recent logs (implement pagination)
 */
router.get('/logs', (req, res) => {
  try {
    const { level: _level, limit: _limit = 100, offset: _offset = 0 } = req.query;

    // This is a placeholder - implement actual log retrieval
    // You might want to use a log aggregation service or database

    res.json({
      logs: [],
      total: 0,
      message: 'Log retrieval not implemented. Use external log aggregation service.',
    });
  } catch (error) {
    logger.error('Failed to get logs', { error: error.message });
    res.status(500).json({ error: 'Failed to fetch logs' });
  }
});

/**
 * GET /api/monitoring/system
 * Get system health and metrics
 */
router.get('/system', (req, res) => {
  try {
    const system = {
      ...performanceMonitor.getSystemStats(),
      timestamp: new Date().toISOString(),
      environment: process.env.NODE_ENV,
      platform: process.platform,
      arch: process.arch,
    };

    res.json(system);
  } catch (error) {
    logger.error('Failed to get system metrics', { error: error.message });
    res.status(500).json({ error: 'Failed to fetch system metrics' });
  }
});

/**
 * DELETE /api/monitoring/cache
 * Clear monitoring caches
 */
router.delete('/cache', (req, res) => {
  try {
    performanceMonitor.clearMetrics();
    alertManager.clearHistory();

    logger.info('Monitoring caches cleared');
    res.json({ success: true, message: 'Caches cleared' });
  } catch (error) {
    logger.error('Failed to clear caches', { error: error.message });
    res.status(500).json({ error: 'Failed to clear caches' });
  }
});

export default router;
