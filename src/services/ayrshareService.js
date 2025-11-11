import axios from 'axios';
import { logger } from '../utils/logger.js';

class AyrshareService {
  constructor() {
    this.apiKey = process.env.AYRSHARE_API_KEY;
    this.baseURL = 'https://app.ayrshare.com/api';

    if (!this.apiKey) {
      logger.warn('AYRSHARE_API_KEY not configured');
    }
  }

  async post(params) {
    try {
      if (!this.apiKey) {
        return {
          success: false,
          error: 'Ayrshare API key not configured'
        };
      }

      const { post, platforms, options = {} } = params;

      let platformArray;
      if (typeof platforms === 'string') {
        platformArray = platforms.split(',').map(p => p.trim().toLowerCase());
      } else if (Array.isArray(platforms)) {
        platformArray = platforms.map(p => p.toLowerCase());
      } else {
        throw new Error('Platforms must be string or array');
      }

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

      logger.info('Posting to Ayrshare:', {
        platforms: mappedPlatforms,
        postLength: post.length
      });

      const response = await axios.post(`${this.baseURL}/post`, payload, {
        headers: {
          'Authorization': `Bearer ${this.apiKey}`,
          'Content-Type': 'application/json'
        },
        timeout: 30000
      });

      logger.info('Ayrshare post successful:', response.data.id);

      return {
        success: true,
        data: response.data,
        platforms: mappedPlatforms,
        timestamp: new Date().toISOString()
      };

    } catch (error) {
      logger.error('Ayrshare posting failed:', error.response?.data || error.message);

      return {
        success: false,
        error: error.message,
        details: error.response?.data,
        timestamp: new Date().toISOString()
      };
    }
  }

  async getUserProfile() {
    try {
      if (!this.apiKey) {
        throw new Error('API key not configured');
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
      return {
        success: false,
        error: error.message
      };
    }
  }

  async testConnection() {
    try {
      const result = await this.getUserProfile();
      return result.success;
    } catch (error) {
      return false;
    }
  }
}

export default new AyrshareService();
