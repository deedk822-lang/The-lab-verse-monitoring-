// src/services/mailchimpService.js
import axios from 'axios';
import { logger } from '../utils/logger.js';

class MailChimpService {
  constructor() {
    this.apiKey = process.env.MAILCHIMP_API_KEY;
    this.serverPrefix = process.env.MAILCHIMP_SERVER_PREFIX;
    this.listId = process.env.MAILCHIMP_LIST_ID;
    
    if (!this.apiKey || !this.serverPrefix) {
      logger.warn('MailChimp not configured - API key or server prefix missing');
      this.baseURL = null;
    } else {
      this.baseURL = `https://${this.serverPrefix}.api.mailchimp.com/3.0`;
    }
  }

  async createAndSendCampaign(params) {
    try {
      if (!this.baseURL || !this.listId) {
        throw new Error('MailChimp not configured. Set MAILCHIMP_API_KEY, MAILCHIMP_SERVER_PREFIX, and MAILCHIMP_LIST_ID');
      }

      const { subject, content, fromName, replyTo, sendNow = true } = params;

      logger.info('Creating MailChimp campaign:', { subject, sendNow });

      // Create campaign
      const campaignResponse = await axios.post(
        `${this.baseURL}/campaigns`,
        {
          type: 'regular',
          recipients: { list_id: this.listId },
          settings: {
            subject_line: subject,
            from_name: fromName || 'AI Content Suite',
            reply_to: replyTo || process.env.MAILCHIMP_REPLY_TO || 'noreply@example.com',
            title: `Campaign: ${subject}`
          }
        },
        {
          headers: {
            Authorization: `Bearer ${this.apiKey}`,
            'Content-Type': 'application/json'
          }
        }
      );

      const campaignId = campaignResponse.data.id;
      logger.info('Campaign created:', campaignId);

      // Set content
      await axios.put(
        `${this.baseURL}/campaigns/${campaignId}/content`,
        { html: this.formatEmailContent(content) },
        {
          headers: {
            Authorization: `Bearer ${this.apiKey}`,
            'Content-Type': 'application/json'
          }
        }
      );

      logger.info('Campaign content set');

      // Send campaign if requested
      if (sendNow) {
        await axios.post(
          `${this.baseURL}/campaigns/${campaignId}/actions/send`,
          {},
          {
            headers: {
              Authorization: `Bearer ${this.apiKey}`,
              'Content-Type': 'application/json'
            }
          }
        );
        logger.info('Campaign sent:', campaignId);
      }

      return {
        success: true,
        data: {
          campaignId,
          sent: sendNow,
          webId: campaignResponse.data.web_id
        }
      };

    } catch (error) {
      logger.error('MailChimp campaign failed:', {
        error: error.message,
        response: error.response?.data
      });

      return {
        success: false,
        error: error.response?.data?.detail || error.message
      };
    }
  }

  formatEmailContent(content) {
    return `
      <!DOCTYPE html>
      <html>
      <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
          body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            margin: 0;
            padding: 0;
          }
          .container {
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
          }
          .content {
            background: #ffffff;
            padding: 30px;
            border-radius: 8px;
          }
          .footer {
            text-align: center;
            padding: 20px;
            color: #666;
            font-size: 12px;
          }
        </style>
      </head>
      <body>
        <div class="container">
          <div class="content">
            ${content.replace(/\n/g, '<br>')}
          </div>
          <div class.footer">
            <p>You received this email because you subscribed to our updates.</p>
          </div>
        </div>
      </body>
      </html>
    `;
  }

  async testConnection() {
    try {
      if (!this.baseURL || !this.listId) {
        return false;
      }

      const result = await this.getListInfo();
      return result.success;
    } catch (error) {
      logger.error('MailChimp connection test failed:', error.message);
      return false;
    }
  }

  async getListInfo() {
    try {
      if (!this.baseURL || !this.listId) {
        throw new Error('MailChimp not configured');
      }

      const response = await axios.get(
        `${this.baseURL}/lists/${this.listId}`,
        {
          headers: {
            Authorization: `Bearer ${this.apiKey}`,
            'Content-Type': 'application/json'
          }
        }
      );

      return {
        success: true,
        data: {
          name: response.data.name,
          memberCount: response.data.stats.member_count,
          id: response.data.id
        }
      };
    } catch (error) {
      logger.error('Failed to get list info:', error.message);
      return {
        success: false,
        error: error.response?.data?.detail || error.message
      };
    }
  }
}

export default new MailChimpService();