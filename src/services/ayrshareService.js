import axios from 'axios';
import { logger } from '../utils/logger.js';

class AyrshareService {
  constructor() {
    this.apiKey = process.env.AYRSHARE_API_KEY;
    this.baseURL = 'https://app.ayrshare.com/api';
    
    if (!this.apiKey) {
      logger.warn('AYRSHARE_API_KEY not found in environment variables');
    }
  }

  /**
   * Post content to multiple social media platforms
   * @param {Object} params - Posting parameters
   * @param {string} params.post - The content to post
   * @param {string|Array} params.platforms - Comma-separated string or array of platforms
   * @param {string} params.mediaUrl - Optional media URL
   * @param {Object} params.options - Additional posting options
   * @returns {Promise<Object>} - API response
   */
  async post(params) {
    try {
      if (!this.apiKey) {
        throw new Error('Ayrshare API key not configured');
      }

      const { post, platforms, mediaUrl, options = {} } = params;
      
      // Normalize platforms to array
      let platformArray;
      if (typeof platforms === 'string') {
        platformArray = platforms.split(',').map(p => p.trim().toLowerCase());
      } else if (Array.isArray(platforms)) {
        platformArray = platforms.map(p => p.toLowerCase());
      } else {
        throw new Error('Platforms must be a string or array');
      }

      // Map platform names to Ayrshare format
      const platformMap = {
        'twitter': 'twitter',
        'facebook': 'facebook',
        'linkedin': 'linkedin',
        'instagram': 'instagram',
        'youtube': 'youtube',
        'tiktok': 'tiktok',
        'telegram': 'telegram',
        'reddit': 'reddit'
      };

      const mappedPlatforms = platformArray
        .map(p => platformMap[p])
        .filter(p => p !== undefined);

      if (mappedPlatforms.length === 0) {
        throw new Error('No valid platforms specified');
      }

      const payload = {
        post,
        platforms: mappedPlatforms,
        ...options
      };

      // Add media if provided
      if (mediaUrl) {
        payload.mediaUrls = [mediaUrl];
      }

      logger.info('Posting to Ayrshare:', {
        platforms: mappedPlatforms,
        postLength: post.length,
        hasMedia: !!mediaUrl
      });

      const response = await axios.post(`${this.baseURL}/post`, payload, {
        headers: {
          'Authorization': `Bearer ${this.apiKey}`,
          'Content-Type': 'application/json'
        },
        timeout: 30000 // 30 second timeout
      });

      logger.info('Ayrshare post successful:', {
        id: response.data.id,
        status: response.data.status,
        platforms: response.data.platforms
      });

      return {
        success: true,
        data: response.data,
        platforms: mappedPlatforms,
        timestamp: new Date().toISOString()
      };

    } catch (error) {
      logger.error('Ayrshare posting failed:', {
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
   * Get post status and analytics
   * @param {string} postId - The post ID returned from the post method
   * @returns {Promise<Object>} - Post status and analytics
   */
  async getPostStatus(postId) {
    try {
      if (!this.apiKey) {
        throw new Error('Ayrshare API key not configured');
      }

      const response = await axios.get(`${this.baseURL}/post/${postId}`, {
        headers: {
          'Authorization': `Bearer ${this.apiKey}`
        }
      });

      return {
        success: true,
        data: response.data
      };

    } catch (error) {
      logger.error('Failed to get post status:', {
        postId,
        error: error.message
      });

      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Get user profile information
   * @returns {Promise<Object>} - User profile data
   */
  async getUserProfile() {
    try {
      if (!this.apiKey) {
        throw new Error('Ayrshare API key not configured');
      }

      const response = await axios.get(`${this.baseURL}/user`, {
        headers: {
          'Authorization': `Bearer ${this.apiKey}`
        }
      });

      return {
        success: true,
        data: response.data
      };

    } catch (error) {
      logger.error('Failed to get user profile:', {
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
      const result = await this.getUserProfile();
      return result.success;
    } catch (error) {
      logger.error('Ayrshare connection test failed:', error.message);
      return false;
    }
  }
}

// Export singleton instance
export default new AyrshareService();