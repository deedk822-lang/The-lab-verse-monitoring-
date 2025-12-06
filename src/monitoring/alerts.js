import { logger } from './logger.js';
import nodemailer from 'nodemailer';

/**
 * Alert severity levels
 */
export const AlertSeverity = {
  LOW: 'low',
  MEDIUM: 'medium',
  HIGH: 'high',
  CRITICAL: 'critical'
};

/**
 * Alert channels
 */
export const AlertChannel = {
  EMAIL: 'email',
  SLACK: 'slack',
  WEBHOOK: 'webhook',
  LOG: 'log'
};

/**
 * Alert manager class
 */
export class AlertManager {
  constructor(config = {}) {
    this.config = {
      email: {
        enabled: process.env.ALERT_EMAIL_ENABLED === 'true',
        from: process.env.ALERT_EMAIL_FROM,
        to: process.env.ALERT_EMAIL_TO?.split(',') || [],
        smtp: {
          host: process.env.SMTP_HOST,
          port: parseInt(process.env.SMTP_PORT || '587'),
          secure: process.env.SMTP_SECURE === 'true',
          auth: {
            user: process.env.SMTP_USER,
            pass: process.env.SMTP_PASS
          }
        }
      },
      slack: {
        enabled: process.env.ALERT_SLACK_ENABLED === 'true',
        webhookUrl: process.env.SLACK_WEBHOOK_URL
      },
      webhook: {
        enabled: process.env.ALERT_WEBHOOK_ENABLED === 'true',
        url: process.env.ALERT_WEBHOOK_URL
      },
      ...config
    };

    this.alertHistory = [];
    this.maxHistorySize = 1000;
    this.cooldowns = new Map(); // Prevent alert spam
    this.cooldownPeriod = 300000; // 5 minutes

    // Initialize email transporter
    if (this.config.email.enabled) {
      this.emailTransporter = nodemailer.createTransport(this.config.email.smtp);
    }
  }

  /**
   * Send an alert
   */
  async sendAlert(alert) {
    const {
      title,
      message,
      severity = AlertSeverity.MEDIUM,
      metadata = {},
      channels = [AlertChannel.LOG]
    } = alert;

    // Check cooldown
    const cooldownKey = `${title}-${severity}`;
    if (this.isInCooldown(cooldownKey)) {
      logger.debug('Alert suppressed due to cooldown', { title, severity });
      return;
    }

    // Create alert object
    const alertObj = {
      id: this.generateAlertId(),
      timestamp: new Date().toISOString(),
      title,
      message,
      severity,
      metadata,
      channels
    };

    // Store in history
    this.addToHistory(alertObj);

    // Set cooldown
    this.setCooldown(cooldownKey);

    // Send to channels
    const promises = channels.map(channel => {
      switch (channel) {
        case AlertChannel.EMAIL:
          return this.sendEmailAlert(alertObj);
        case AlertChannel.SLACK:
          return this.sendSlackAlert(alertObj);
        case AlertChannel.WEBHOOK:
          return this.sendWebhookAlert(alertObj);
        case AlertChannel.LOG:
          return this.logAlert(alertObj);
        default:
          logger.warn('Unknown alert channel', { channel });
          return Promise.resolve();
      }
    });

    await Promise.allSettled(promises);

    logger.info('Alert sent', {
      id: alertObj.id,
      title,
      severity,
      channels: channels.join(',')
    });

    return alertObj;
  }

  /**
   * Send email alert
   */
  async sendEmailAlert(alert) {
    if (!this.config.email.enabled || !this.emailTransporter) {
      return;
    }

    try {
      const severityEmoji = {
        [AlertSeverity.LOW]: '🔵',
        [AlertSeverity.MEDIUM]: '🟡',
        [AlertSeverity.HIGH]: '🟠',
        [AlertSeverity.CRITICAL]: '🔴'
      };

      const html = `
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
          <h2 style="color: #333;">
            ${severityEmoji[alert.severity]} ${alert.title}
          </h2>
          <p style="color: #666; font-size: 14px;">
            <strong>Severity:</strong> ${alert.severity.toUpperCase()}<br>
            <strong>Time:</strong> ${alert.timestamp}
          </p>
          <div style="background: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0;">
            <p style="margin: 0; color: #333;">${alert.message}</p>
          </div>
          ${Object.keys(alert.metadata).length > 0 ? `
            <h3 style="color: #333;">Additional Details:</h3>
            <pre style="background: #f5f5f5; padding: 15px; border-radius: 5px; overflow-x: auto;">
${JSON.stringify(alert.metadata, null, 2)}
            </pre>
          ` : ''}
        </div>
      `;

      await this.emailTransporter.sendMail({
        from: this.config.email.from,
        to: this.config.email.to,
        subject: `[${alert.severity.toUpperCase()}] ${alert.title}`,
        html
      });

      logger.debug('Email alert sent', { id: alert.id });

    } catch (error) {
      logger.error('Failed to send email alert', { error: error.message, alert });
    }
  }

  /**
   * Send Slack alert
   */
  async sendSlackAlert(alert) {
    if (!this.config.slack.enabled) {
      return;
    }

    try {
      const colorMap = {
        [AlertSeverity.LOW]: '#36a64f',
        [AlertSeverity.MEDIUM]: '#ff9900',
        [AlertSeverity.HIGH]: '#ff6600',
        [AlertSeverity.CRITICAL]: '#ff0000'
      };

      const payload = {
        attachments: [{
          color: colorMap[alert.severity],
          title: alert.title,
          text: alert.message,
          fields: [
            {
              title: 'Severity',
              value: alert.severity.toUpperCase(),
              short: true
            },
            {
              title: 'Time',
              value: alert.timestamp,
              short: true
            },
            ...Object.entries(alert.metadata).map(([key, value]) => ({
              title: key,
              value: typeof value === 'object' ? JSON.stringify(value) : String(value),
              short: false
            }))
          ],
          footer: 'Lab Verse Monitoring',
          ts: Math.floor(Date.now() / 1000)
        }]
      };

      const response = await fetch(this.config.slack.webhookUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        throw new Error(`Slack API error: ${response.status}`);
      }

      logger.debug('Slack alert sent', { id: alert.id });

    } catch (error) {
      logger.error('Failed to send Slack alert', { error: error.message, alert });
    }
  }

  /**
   * Send webhook alert
   */
  async sendWebhookAlert(alert) {
    if (!this.config.webhook.enabled) {
      return;
    }

    try {
      const response = await fetch(this.config.webhook.url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(alert)
      });

      if (!response.ok) {
        throw new Error(`Webhook error: ${response.status}`);
      }

      logger.debug('Webhook alert sent', { id: alert.id });

    } catch (error) {
      logger.error('Failed to send webhook alert', { error: error.message, alert });
    }
  }

  /**
   * Log alert
   */
  logAlert(alert) {
    const logMethod = {
      [AlertSeverity.LOW]: 'info',
      [AlertSeverity.MEDIUM]: 'warn',
      [AlertSeverity.HIGH]: 'error',
      [AlertSeverity.CRITICAL]: 'error'
    }[alert.severity];

    logger[logMethod](`ALERT: ${alert.title}`, {
      message: alert.message,
      severity: alert.severity,
      metadata: alert.metadata
    });

    return Promise.resolve();
  }

  /**
   * Check if alert is in cooldown
   */
  isInCooldown(key) {
    const cooldownUntil = this.cooldowns.get(key);
    if (!cooldownUntil) return false;

    if (Date.now() < cooldownUntil) {
      return true;
    }

    this.cooldowns.delete(key);
    return false;
  }

  /**
   * Set cooldown for alert
   */
  setCooldown(key) {
    this.cooldowns.set(key, Date.now() + this.cooldownPeriod);
  }

  /**
   * Generate unique alert ID
   */
  generateAlertId() {
    return `alert_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Add alert to history
   */
  addToHistory(alert) {
    this.alertHistory.unshift(alert);

    // Trim history if too large
    if (this.alertHistory.length > this.maxHistorySize) {
      this.alertHistory = this.alertHistory.slice(0, this.maxHistorySize);
    }
  }

  /**
   * Get alert history
   */
  getHistory(filters = {}) {
    let history = [...this.alertHistory];

    if (filters.severity) {
      history = history.filter(a => a.severity === filters.severity);
    }

    if (filters.since) {
      const sinceTime = new Date(filters.since).getTime();
      history = history.filter(a => new Date(a.timestamp).getTime() >= sinceTime);
    }

    if (filters.limit) {
      history = history.slice(0, filters.limit);
    }

    return history;
  }

  /**
   * Get alert statistics
   */
  getStats(period = 3600000) { // Default 1 hour
    const since = Date.now() - period;
    const recentAlerts = this.alertHistory.filter(
      a => new Date(a.timestamp).getTime() >= since
    );

    const stats = {
      total: recentAlerts.length,
      bySeverity: {
        [AlertSeverity.LOW]: 0,
        [AlertSeverity.MEDIUM]: 0,
        [AlertSeverity.HIGH]: 0,
        [AlertSeverity.CRITICAL]: 0
      },
      byChannel: {},
      period: `${period / 1000}s`
    };

    recentAlerts.forEach(alert => {
      stats.bySeverity[alert.severity]++;

      alert.channels.forEach(channel => {
        stats.byChannel[channel] = (stats.byChannel[channel] || 0) + 1;
      });
    });

    return stats;
  }

  /**
   * Clear alert history
   */
  clearHistory() {
    this.alertHistory = [];
    logger.info('Alert history cleared');
  }
}

// Export singleton instance
export const alertManager = new AlertManager();

/**
 * Convenience functions for common alerts
 */
export async function alertHighErrorRate(errorRate, threshold) {
  return alertManager.sendAlert({
    title: 'High Error Rate Detected',
    message: `Error rate (${errorRate.toFixed(2)}%) exceeds threshold (${threshold}%)`,
    severity: errorRate > threshold * 2 ? AlertSeverity.CRITICAL : AlertSeverity.HIGH,
    metadata: { errorRate, threshold },
    channels: [AlertChannel.EMAIL, AlertChannel.SLACK, AlertChannel.LOG]
  });
}

export async function alertHighCost(cost, threshold) {
  return alertManager.sendAlert({
    title: 'High Cost Alert',
    message: `Total cost ($${cost.toFixed(2)}) exceeds threshold ($${threshold})`,
    severity: cost > threshold * 1.5 ? AlertSeverity.CRITICAL : AlertSeverity.HIGH,
    metadata: { cost, threshold },
    channels: [AlertChannel.EMAIL, AlertChannel.SLACK, AlertChannel.LOG]
  });
}

export async function alertServiceDown(serviceName, details = {}) {
  return alertManager.sendAlert({
    title: `Service Down: ${serviceName}`,
    message: `The ${serviceName} service is not responding`,
    severity: AlertSeverity.CRITICAL,
    metadata: { service: serviceName, ...details },
    channels: [AlertChannel.EMAIL, AlertChannel.SLACK, AlertChannel.LOG]
  });
}

export async function alertSlowResponse(endpoint, duration, threshold) {
  return alertManager.sendAlert({
    title: 'Slow Response Time',
    message: `Endpoint ${endpoint} responded in ${duration}ms (threshold: ${threshold}ms)`,
    severity: duration > threshold * 2 ? AlertSeverity.HIGH : AlertSeverity.MEDIUM,
    metadata: { endpoint, duration, threshold },
    channels: [AlertChannel.LOG, AlertChannel.SLACK]
  });
}
