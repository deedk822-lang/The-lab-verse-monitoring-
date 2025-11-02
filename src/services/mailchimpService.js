import axios from 'axios';
import { logger } from '../utils/logger.js';

class MailChimpService {
  constructor() {
    this.apiKey = process.env.MAILCHIMP_API_KEY;
    this.serverPrefix = process.env.MAILCHIMP_SERVER_PREFIX; // e.g., 'us1', 'us2', etc.
    this.listId = process.env.MAILCHIMP_LIST_ID;
    
    if (!this.apiKey) {
      logger.warn('MAILCHIMP_API_KEY not found in environment variables');
    }
    
    if (!this.serverPrefix) {
      logger.warn('MAILCHIMP_SERVER_PREFIX not found in environment variables');
    }
    
    if (this.apiKey && this.serverPrefix) {
      this.baseURL = `https://${this.serverPrefix}.api.mailchimp.com/3.0`;
    }
  }

  /**
   * Create and send an email campaign
   * @param {Object} params - Campaign parameters
   * @param {string} params.subject - Email subject line
   * @param {string} params.content - Email content (HTML or text)
   * @param {string} params.fromName - Sender name
   * @param {string} params.replyTo - Reply-to email address
   * @param {string} params.listId - MailChimp list ID (optional, uses default)
   * @param {boolean} params.sendNow - Whether to send immediately
   * @returns {Promise<Object>} - Campaign creation and send result
   */
  async createAndSendCampaign(params) {
    try {
      if (!this.apiKey || !this.serverPrefix) {
        throw new Error('MailChimp API key or server prefix not configured');
      }

      const { 
        subject, 
        content, 
        fromName = 'AI Content Suite',
        replyTo = process.env.MAILCHIMP_REPLY_TO || 'noreply@example.com',
        listId = this.listId,
        sendNow = true
      } = params;

      if (!listId) {
        throw new Error('MailChimp list ID not configured');
      }

      logger.info('Creating MailChimp campaign:', {
        subject,
        listId,
        fromName,
        contentLength: content.length
      });

      // Step 1: Create campaign
      const campaignData = {
        type: 'regular',
        recipients: {
          list_id: listId
        },
        settings: {
          subject_line: subject,
          from_name: fromName,
          reply_to: replyTo,
          auto_footer: false,
          inline_css: true
        }
      };

      const campaignResponse = await axios.post(
        `${this.baseURL}/campaigns`,
        campaignData,
        {
          headers: {
            'Authorization': `Bearer ${this.apiKey}`,
            'Content-Type': 'application/json'
          }
        }
      );

      const campaignId = campaignResponse.data.id;
      
      logger.info('MailChimp campaign created:', { campaignId });

      // Step 2: Set campaign content
      const contentData = {
        html: this.formatContentAsHTML(content, subject)
      };

      await axios.put(
        `${this.baseURL}/campaigns/${campaignId}/content`,
        contentData,
        {
          headers: {
            'Authorization': `Bearer ${this.apiKey}`,
            'Content-Type': 'application/json'
          }
        }
      );

      logger.info('MailChimp campaign content set:', { campaignId });

      let sendResult = null;
      
      // Step 3: Send campaign if requested
      if (sendNow) {
        const sendResponse = await axios.post(
          `${this.baseURL}/campaigns/${campaignId}/actions/send`,
          {},
          {
            headers: {
              'Authorization': `Bearer ${this.apiKey}`,
              'Content-Type': 'application/json'
            }
          }
        );

        sendResult = sendResponse.data;
        logger.info('MailChimp campaign sent:', { campaignId });
      }

      return {
        success: true,
        data: {
          campaignId,
          campaign: campaignResponse.data,
          sent: sendNow,
          sendResult
        },
        timestamp: new Date().toISOString()
      };

    } catch (error) {
      logger.error('MailChimp campaign failed:', {
        error: error.message,
        response: error.response?.data,
        status: error.response?.status
      });

      return {
        success: false,
        error: error.message,
        details: error.response?.data,
        timestamp: new Date().toISOString()
      };
    }
  }

  /**
   * Format content as HTML email
   * @param {string} content - Plain text or markdown content
   * @param {string} title - Email title
   * @returns {string} - Formatted HTML
   */
  formatContentAsHTML(content, title) {
    // Basic HTML email template
    return `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>${title}</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f4f4f4;
        }
        .container {
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .header {
            text-align: center;
            border-bottom: 2px solid #007bff;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }
        .content {
            white-space: pre-wrap;
            word-wrap: break-word;
        }
        .footer {
            text-align: center;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #eee;
            font-size: 12px;
            color: #666;
        }
        a {
            color: #007bff;
            text-decoration: none;
        }
        a:hover {
            text-decoration: underline;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>${title}</h1>
        </div>
        <div class="content">
            ${this.convertToHTML(content)}
        </div>
        <div class="footer">
            <p>Generated by AI Content Creation Suite</p>
            <p>Powered by artificial intelligence</p>
        </div>
    </div>
</body>
</html>`;
  }

  /**
   * Convert plain text to basic HTML
   * @param {string} text - Plain text content
   * @returns {string} - Basic HTML
   */
  convertToHTML(text) {
    return text
      .replace(/\n\n/g, '</p><p>')
      .replace(/\n/g, '<br>')
      .replace(/^/, '<p>')
      .replace(/$/, '</p>')
      .replace(/<p><\/p>/g, '')
      // Basic markdown-like formatting
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/`(.*?)`/g, '<code>$1</code>');
  }

  /**
   * Get campaign statistics
   * @param {string} campaignId - Campaign ID
   * @returns {Promise<Object>} - Campaign stats
   */
  async getCampaignStats(campaignId) {
    try {
      if (!this.apiKey) {
        throw new Error('MailChimp API key not configured');
      }

      const response = await axios.get(
        `${this.baseURL}/reports/${campaignId}`,
        {
          headers: {
            'Authorization': `Bearer ${this.apiKey}`
          }
        }
      );

      return {
        success: true,
        data: response.data
      };

    } catch (error) {
      logger.error('Failed to get campaign stats:', {
        campaignId,
        error: error.message
      });

      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Get list information
   * @param {string} listId - List ID (optional, uses default)
   * @returns {Promise<Object>} - List information
   */
  async getListInfo(listId = this.listId) {
    try {
      if (!this.apiKey) {
        throw new Error('MailChimp API key not configured');
      }

      if (!listId) {
        throw new Error('List ID not provided or configured');
      }

      const response = await axios.get(
        `${this.baseURL}/lists/${listId}`,
        {
          headers: {
            'Authorization': `Bearer ${this.apiKey}`
          }
        }
      );

      return {
        success: true,
        data: response.data
      };

    } catch (error) {
      logger.error('Failed to get list info:', {
        listId,
        error: error.message
      });

      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Test the API connection
   * @returns {Promise<boolean>} - Connection status
   */
  async testConnection() {
    try {
      if (!this.apiKey || !this.serverPrefix) {
        return false;
      }

      const response = await axios.get(
        `${this.baseURL}/ping`,
        {
          headers: {
            'Authorization': `Bearer ${this.apiKey}`
          }
        }
      );

      return response.data.health_status === 'Everything\'s Chimpy!';
    } catch (error) {
      logger.error('MailChimp connection test failed:', error.message);
      return false;
    }
  }

  /**
   * Add subscriber to list
   * @param {Object} params - Subscriber parameters
   * @param {string} params.email - Email address
   * @param {string} params.firstName - First name (optional)
   * @param {string} params.lastName - Last name (optional)
   * @param {string} params.listId - List ID (optional, uses default)
   * @returns {Promise<Object>} - Subscription result
   */
  async addSubscriber(params) {
    try {
      if (!this.apiKey) {
        throw new Error('MailChimp API key not configured');
      }

      const { email, firstName, lastName, listId = this.listId } = params;

      if (!listId) {
        throw new Error('List ID not provided or configured');
      }

      const subscriberData = {
        email_address: email,
        status: 'subscribed',
        merge_fields: {}
      };

      if (firstName) subscriberData.merge_fields.FNAME = firstName;
      if (lastName) subscriberData.merge_fields.LNAME = lastName;

      const response = await axios.post(
        `${this.baseURL}/lists/${listId}/members`,
        subscriberData,
        {
          headers: {
            'Authorization': `Bearer ${this.apiKey}`,
            'Content-Type': 'application/json'
          }
        }
      );

      return {
        success: true,
        data: response.data
      };

    } catch (error) {
      logger.error('Failed to add subscriber:', {
        email: params.email,
        error: error.message
      });

      return {
        success: false,
        error: error.message
      };
    }
  }
}

// Export singleton instance
export default new MailChimpService();