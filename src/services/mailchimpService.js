import axios from 'axios';
import { logger } from '../utils/logger.js';

class MailChimpService {
  constructor() {
    this.apiKey = process.env.MAILCHIMP_API_KEY;
    this.serverPrefix = process.env.MAILCHIMP_SERVER_PREFIX;
    this.listId = process.env.MAILCHIMP_LIST_ID;
    this.baseURL = this.serverPrefix ? 
      `https://${this.serverPrefix}.api.mailchimp.com/3.0` : null;
    
    if (!this.apiKey || !this.serverPrefix || !this.listId) {
      logger.warn('MailChimp not fully configured');
    }
  }

  async createAndSendCampaign(params) {
    try {
      if (!this.apiKey || !this.baseURL || !this.listId) {
        return {
          success: false,
          error: 'MailChimp not configured'
        };
      }

      const { subject, content, fromName, replyTo, sendNow = true } = params;
      
      // Create campaign
      const campaign = await axios.post(
        `${this.baseURL}/campaigns`,
        {
          type: 'regular',
          recipients: { list_id: this.listId },
          settings: {
            subject_line: subject,
            from_name: fromName || 'AI Content Suite',
            reply_to: replyTo || 'noreply@example.com',
            title: `Campaign: ${subject}`
          }
        },
        {
          headers: { Authorization: `Bearer ${this.apiKey}` }
        }
      );

      const campaignId = campaign.data.id;

      // Set content
      await axios.put(
        `${this.baseURL}/campaigns/${campaignId}/content`,
        { html: this.formatEmailContent(content) },
        {
          headers: { Authorization: `Bearer ${this.apiKey}` }
        }
      );

      // Send if requested
      if (sendNow) {
        await axios.post(
          `${this.baseURL}/campaigns/${campaignId}/actions/send`,
          {},
          {
            headers: { Authorization: `Bearer ${this.apiKey}` }
          }
        );
      }

      return {
        success: true,
        data: { campaignId, sent: sendNow }
      };

    } catch (error) {
      logger.error('MailChimp campaign failed:', error.response?.data || error.message);
      return {
        success: false,
        error: error.message
      };
    }
  }

  formatEmailContent(content) {
    return `
      <!DOCTYPE html>
      <html>
      <head>
        <meta charset="UTF-8">
        <style>
          body { font-family: Arial, sans-serif; line-height: 1.6; }
          .content { padding: 20px; max-width: 600px; margin: 0 auto; }
        </style>
      </head>
      <body>
        <div class="content">
          ${content.replace(/\n/g, '<br>')}
        </div>
      </body>
      </html>
    `;
  }

  async testConnection() {
    try {
      const result = await this.getListInfo();
      return result.success;
    } catch (error) {
      return false;
    }
  }

  async getListInfo() {
    try {
      if (!this.apiKey || !this.baseURL || !this.listId) {
        throw new Error('Not configured');
      }

      const response = await axios.get(
        `${this.baseURL}/lists/${this.listId}`,
        {
          headers: { Authorization: `Bearer ${this.apiKey}` }
        }
      );

      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }
}

export default new MailChimpService();
