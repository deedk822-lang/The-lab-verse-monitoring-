/**
 * Vercel Speed Insights Integration for Express
 * This module provides server-side integration with Vercel Speed Insights
 * to track performance metrics for the monitoring system.
 */

import { injectSpeedInsights } from '@vercel/speed-insights';

/**
 * Initialize Speed Insights for server-side performance tracking
 * This function should be called once during application startup
 */
export function initializeSpeedInsights() {
  try {
    injectSpeedInsights();
    console.log('✓ Speed Insights initialized successfully');
  } catch (error) {
    console.warn('⚠ Speed Insights initialization failed:', error.message);
    // Don't throw - Speed Insights is optional and shouldn't break the app
  }
}

/**
 * Middleware to track request performance metrics
 * Measures response times and sends metrics to Speed Insights
 */
export function speedInsightsMiddleware(req, res, next) {
  const startTime = Date.now();

  // Override res.end to capture the response
  const originalEnd = res.end;
  res.end = function (...args) {
    const duration = Date.now() - startTime;

    // Track performance data
    if (window?.si) {
      window.si('pageview', {
        route: req.path,
        method: req.method,
        duration: duration,
        status: res.statusCode,
      });
    }

    originalEnd.apply(res, args);
  };

  next();
}

export default initializeSpeedInsights;
