import { injectSpeedInsights } from '@vercel/speed-insights';

// Initialize Speed Insights
export function initializeSpeedInsights() {
  if (typeof window !== 'undefined') {
    injectSpeedInsights({
      framework: 'express',
      debug: process.env.NODE_ENV === 'development',
      beforeSend: (metric) => {
        // Filter out metrics from bots
        if (navigator.userAgent.includes('bot')) {
          return null;
        }

        // Add custom data
        metric.customData = {
          environment: process.env.NODE_ENV,
          version: process.env.npm_package_version
        };

        return metric;
      }
    });

    console.log('✅ Speed Insights initialized');
  }
}

// Track custom Web Vitals
export function trackCustomMetric(name, value, metadata = {}) {
  if (typeof window !== 'undefined' && window.webVitals) {
    window.webVitals.push({
      name,
      value,
      metadata,
      timestamp: Date.now()
    });
  }
}
