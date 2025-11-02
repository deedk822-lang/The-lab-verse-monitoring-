import axios from 'axios';
import crypto from 'crypto';
import { logger } from '../utils/logger.js';

class A2AService {
  constructor() {
    this.apiKey = process.env.A2A_API_KEY;
    this.secretKey = process.env.A2A_SECRET_KEY;
    this.baseURL = process.env.A2A_BASE_URL || 'https://api.a2a.ai/v1';
    this.clientId = process.env.A2A_CLIENT_ID;
    
    // Application endpoints configuration
    this.endpoints = {
      slack: process.env.A2A_SLACK_WEBHOOK,
      teams: process.env.A2A_TEAMS_WEBHOOK,
      discord: process.env.A2A_DISCORD_WEBHOOK,
      zapier: process.env.A2A_ZAPIER_WEBHOOK,
      ifttt: process.env.A2A_IFTTT_WEBHOOK,
      n8n: process.env.A2A_N8N_WEBHOOK,
      make: process.env.A2A_MAKE_WEBHOOK
    };
    
    if (!this.apiKey) {
      logger.warn('A2A_API_KEY not found in environment variables');
    }
  }

  /**
   * Generate secure signature for A2A communication
   * @param {string} payload - Request payload
   * @param {number} timestamp - Unix timestamp
   * @returns {string} - HMAC signature
   */
  generateSignature(payload, timestamp) {
    if (!this.secretKey) {
      throw new Error('A2A secret key not configured');
    }
    
    const message = `${timestamp}.${payload}`;
    return crypto
      .createHmac('sha256', this.secretKey)
      .update(message)
      .digest('hex');
  }

  /**
   * Send content to multiple applications via A2A protocol
   * @param {Object} params - Distribution parameters
   * @param {string} params.content - Content to distribute
   * @param {Array} params.targets - Target applications
   * @param {Object} params.metadata - Additional metadata
   * @param {string} params.priority - Message priority (low, normal, high)
   * @returns {Promise<Object>} - Distribution result
   */
  async distributeContent(params) {
    try {
      const {
        content,
        targets = [],
        metadata = {},
        priority = 'normal',
        includeAnalytics = true,
        batchMode = true
      } = params;

      if (targets.length === 0) {
        throw new Error('No target applications specified');
      }

      const timestamp = Math.floor(Date.now() / 1000);
      const payload = JSON.stringify({
        content,
        metadata: {
          ...metadata,
          timestamp,
          priority,
          source: 'ai-content-suite',
          version: '1.0.0'
        },
        targets,
        options: {
          includeAnalytics,
          batchMode
        }
      });

      const signature = this.generateSignature(payload, timestamp);

      logger.info('Distributing content via A2A:', {
        targets,
        contentLength: content.length,
        priority,
        batchMode
      });

      const results = {};

      if (batchMode && this.apiKey) {
        // Use A2A service for batch distribution
        const response = await axios.post(`${this.baseURL}/distribute`, {
          payload: JSON.parse(payload)
        }, {
          headers: {
            'Authorization': `Bearer ${this.apiKey}`,
            'X-A2A-Signature': `sha256=${signature}`,
            'X-A2A-Timestamp': timestamp,
            'X-A2A-Client-ID': this.clientId,
            'Content-Type': 'application/json'
          },
          timeout: 60000
        });

        results.batch = response.data;
      } else {
        // Direct distribution to individual targets
        const promises = targets.map(target => this.sendToTarget({
          target,
          content,
          metadata,
          signature,
          timestamp
        }));

        const targetResults = await Promise.allSettled(promises);
        
        targetResults.forEach((result, index) => {
          const target = targets[index];
          results[target] = result.status === 'fulfilled' 
            ? result.value 
            : { success: false, error: result.reason.message };
        });
      }

      const successCount = Object.values(results).filter(r => r.success !== false).length;
      
      logger.info('A2A distribution completed:', {
        totalTargets: targets.length,
        successful: successCount,
        failed: targets.length - successCount
      });

      return {
        success: successCount > 0,
        results,
        summary: {
          total: targets.length,
          successful: successCount,
          failed: targets.length - successCount
        },
        timestamp: new Date().toISOString()
      };

    } catch (error) {
      logger.error('A2A distribution failed:', {
        error: error.message,
        targets: params.targets
      });

      return {
        success: false,
        error: error.message,
        timestamp: new Date().toISOString()
      };
    }
  }

  /**
   * Send content to a specific target application
   * @param {Object} params - Target-specific parameters
   * @returns {Promise<Object>} - Send result
   */
  async sendToTarget(params) {
    try {
      const { target, content, metadata, signature, timestamp } = params;
      
      const endpoint = this.endpoints[target.toLowerCase()];
      if (!endpoint) {
        throw new Error(`No endpoint configured for target: ${target}`);
      }

      const payload = {
        text: content,
        metadata,
        timestamp,
        source: 'ai-content-suite'
      };

      // Customize payload based on target platform
      const customizedPayload = this.customizeForTarget(target, payload);

      const response = await axios.post(endpoint, customizedPayload, {
        headers: {
          'Content-Type': 'application/json',
          'X-A2A-Signature': `sha256=${signature}`,
          'X-A2A-Timestamp': timestamp,
          'User-Agent': 'AI-Content-Suite/1.0'
        },
        timeout: 30000
      });

      return {
        success: true,
        target,
        response: response.data,
        statusCode: response.status
      };

    } catch (error) {
      logger.error(`Failed to send to ${params.target}:`, error.message);
      return {
        success: false,
        target: params.target,
        error: error.message
      };
    }
  }

  /**
   * Customize payload for specific target platforms
   * @param {string} target - Target platform
   * @param {Object} payload - Original payload
   * @returns {Object} - Customized payload
   */
  customizeForTarget(target, payload) {
    const { text, metadata } = payload;
    
    switch (target.toLowerCase()) {
      case 'slack':
        return {
          text,
          blocks: [
            {
              type: 'section',
              text: {
                type: 'mrkdwn',
                text
              }
            }
          ],
          metadata
        };

      case 'teams':
        return {
          '@type': 'MessageCard',
          '@context': 'https://schema.org/extensions',
          text,
          themeColor: '0078D4',
          sections: [{
            text,
            metadata
          }]
        };

      case 'discord':
        return {
          content: text,
          embeds: [{
            description: text.substring(0, 2048), // Discord embed limit
            timestamp: new Date().toISOString(),
            footer: {
              text: 'AI Content Suite'
            }
          }]
        };

      case 'zapier':
      case 'ifttt':
      case 'n8n':
      case 'make':
        return {
          content: text,
          metadata,
          trigger_source: 'ai-content-suite'
        };

      default:
        return payload;
    }
  }

  /**
   * Register webhook callback for bi-directional communication
   * @param {Object} params - Webhook parameters
   * @param {string} params.target - Target application
   * @param {string} params.callbackUrl - Callback URL
   * @param {Array} params.events - Events to subscribe to
   * @returns {Promise<Object>} - Registration result
   */
  async registerWebhook(params) {
    try {
      if (!this.apiKey) {
        throw new Error('A2A API key not configured');
      }

      const { target, callbackUrl, events = ['message', 'status'] } = params;

      const response = await axios.post(`${this.baseURL}/webhooks`, {
        target,
        callback_url: callbackUrl,
        events,
        client_id: this.clientId
      }, {
        headers: {
          'Authorization': `Bearer ${this.apiKey}`,
          'Content-Type': 'application/json'
        }
      });

      logger.info('A2A webhook registered:', { target, events });

      return {
        success: true,
        data: response.data
      };

    } catch (error) {
      logger.error('A2A webhook registration failed:', error.message);
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Get analytics for A2A communications
   * @param {Object} params - Analytics parameters
   * @param {string} params.timeRange - Time range (1h, 24h, 7d, 30d)
   * @param {Array} params.targets - Specific targets to analyze
   * @returns {Promise<Object>} - Analytics data
   */
  async getAnalytics(params = {}) {
    try {
      if (!this.apiKey) {
        throw new Error('A2A API key not configured');
      }

      const { timeRange = '24h', targets = [] } = params;

      const response = await axios.get(`${this.baseURL}/analytics`, {
        params: {
          time_range: timeRange,
          targets: targets.join(','),
          client_id: this.clientId
        },
        headers: {
          'Authorization': `Bearer ${this.apiKey}`
        }
      });

      return {
        success: true,
        data: response.data
      };

    } catch (error) {
      logger.error('A2A analytics fetch failed:', error.message);
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Test connection to A2A service and configured endpoints
   * @returns {Promise<Object>} - Connection test results
   */
  async testConnections() {
    try {
      const results = {
        a2aService: false,
        endpoints: {}
      };

      // Test A2A service connection
      if (this.apiKey) {
        try {
          const response = await axios.get(`${this.baseURL}/health`, {
            headers: {
              'Authorization': `Bearer ${this.apiKey}`
            },
            timeout: 10000
          });
          results.a2aService = response.status === 200;
        } catch (error) {
          logger.warn('A2A service connection test failed:', error.message);
        }
      }

      // Test configured endpoints
      const testPromises = Object.entries(this.endpoints)
        .filter(([, endpoint]) => endpoint)
        .map(async ([target, endpoint]) => {
          try {
            // Simple ping test with minimal payload
            const testPayload = {
              test: true,
              message: 'Connection test from AI Content Suite',
              timestamp: Date.now()
            };

            await axios.post(endpoint, this.customizeForTarget(target, testPayload), {
              timeout: 10000,
              headers: {
                'Content-Type': 'application/json'
              }
            });

            results.endpoints[target] = { success: true, configured: true };
          } catch (error) {
            results.endpoints[target] = { 
              success: false, 
              configured: true,
              error: error.message 
            };
          }
        });

      await Promise.allSettled(testPromises);

      // Add unconfigured endpoints
      Object.keys(this.endpoints).forEach(target => {
        if (!this.endpoints[target] && !results.endpoints[target]) {
          results.endpoints[target] = { success: false, configured: false };
        }
      });

      logger.info('A2A connection tests completed:', results);

      return {
        success: true,
        results
      };

    } catch (error) {
      logger.error('A2A connection tests failed:', error.message);
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Send urgent notification via A2A
   * @param {Object} params - Urgent notification parameters
   * @param {string} params.message - Urgent message
   * @param {Array} params.targets - Priority targets
   * @param {string} params.level - Urgency level (info, warning, critical)
   * @returns {Promise<Object>} - Notification result
   */
  async sendUrgentNotification(params) {
    try {
      const { message, targets = ['slack', 'teams'], level = 'warning' } = params;

      const urgentContent = `🚨 **${level.toUpperCase()}** 🚨\n\n${message}\n\n*Sent via AI Content Suite A2A*`;

      return await this.distributeContent({
        content: urgentContent,
        targets,
        metadata: {
          urgency: level,
          type: 'notification',
          alert: true
        },
        priority: 'high',
        batchMode: false // Send immediately to all targets
      });

    } catch (error) {
      logger.error('A2A urgent notification failed:', error.message);
      return {
        success: false,
        error: error.message
      };
    }
  }
}

// Export singleton instance
export default new A2AService();