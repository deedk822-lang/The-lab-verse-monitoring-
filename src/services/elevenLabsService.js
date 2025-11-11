import axios from 'axios';
import fs from 'fs';
import path from 'path';
import { logger } from '../utils/logger.js';

class ElevenLabsService {
  constructor() {
    this.apiKey = process.env.ELEVENLABS_API_KEY;
    this.baseURL = 'https://api.elevenlabs.io/v1';
    this.defaultVoiceId = process.env.ELEVENLABS_DEFAULT_VOICE_ID || 'pNInz6obpgDQGcFmaJgB'; // Adam voice
    this.outputDir = process.env.UPLOAD_DIR || './uploads';

    // Ensure output directory exists
    if (!fs.existsSync(this.outputDir)) {
      fs.mkdirSync(this.outputDir, { recursive: true });
    }

    if (!this.apiKey) {
      logger.warn('ELEVENLABS_API_KEY not found in environment variables');
    }
  }

  /**
   * Convert text to speech using ElevenLabs
   * @param {Object} params - TTS parameters
   * @param {string} params.text - Text to convert
   * @param {string} params.voiceId - Voice ID to use
   * @param {Object} params.voiceSettings - Voice configuration
   * @param {string} params.outputFormat - Audio format (mp3, wav, etc.)
   * @returns {Promise<Object>} - TTS result with file path
   */
  async textToSpeech(params) {
    try {
      if (!this.apiKey) {
        throw new Error('ElevenLabs API key not configured');
      }

      const {
        text,
        voiceId = this.defaultVoiceId,
        voiceSettings = {
          stability: 0.5,
          similarity_boost: 0.8,
          style: 0.0,
          use_speaker_boost: true
        },
        outputFormat = 'mp3',
        modelId = 'eleven_multilingual_v2'
      } = params;

      if (text.length > 5000) {
        throw new Error('Text too long. Maximum 5000 characters allowed.');
      }

      logger.info('Converting text to speech:', {
        voiceId,
        textLength: text.length,
        modelId,
        outputFormat
      });

      const response = await axios.post(
        `${this.baseURL}/text-to-speech/${voiceId}`,
        {
          text,
          model_id: modelId,
          voice_settings: voiceSettings
        },
        {
          headers: {
            'xi-api-key': this.apiKey,
            'Content-Type': 'application/json',
            'Accept': `audio/${outputFormat}`
          },
          responseType: 'stream',
          timeout: 60000
        }
      );

      // Generate unique filename
      const timestamp = Date.now();
      const filename = `tts_${timestamp}.${outputFormat}`;
      const filepath = path.join(this.outputDir, filename);

      // Save audio file
      const writer = fs.createWriteStream(filepath);
      response.data.pipe(writer);

      await new Promise((resolve, reject) => {
        writer.on('finish', resolve);
        writer.on('error', reject);
      });

      const fileStats = fs.statSync(filepath);

      logger.info('Text-to-speech completed:', {
        filename,
        fileSize: fileStats.size,
        voiceId,
        textLength: text.length
      });

      return {
        success: true,
        audioFile: filename,
        filepath,
        fileSize: fileStats.size,
        duration: this.estimateAudioDuration(text),
        metadata: {
          voiceId,
          modelId,
          textLength: text.length,
          voiceSettings,
          outputFormat,
          timestamp: new Date().toISOString()
        }
      };

    } catch (error) {
      logger.error('Text-to-speech failed:', {
        error: error.message,
        response: error.response?.data
      });

      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Get list of available voices
   * @returns {Promise<Object>} - Available voices
   */
  async getVoices() {
    try {
      if (!this.apiKey) {
        throw new Error('ElevenLabs API key not configured');
      }

      const response = await axios.get(`${this.baseURL}/voices`, {
        headers: {
          'xi-api-key': this.apiKey
        }
      });

      const voices = response.data.voices.map(voice => ({
        id: voice.voice_id,
        name: voice.name,
        category: voice.category,
        description: voice.description,
        labels: voice.labels,
        preview_url: voice.preview_url,
        settings: voice.settings
      }));

      logger.info('Retrieved ElevenLabs voices:', {
        count: voices.length
      });

      return {
        success: true,
        voices
      };

    } catch (error) {
      logger.error('Failed to get voices:', error.message);
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Clone a voice from audio samples
   * @param {Object} params - Voice cloning parameters
   * @param {string} params.name - Voice name
   * @param {Array} params.audioFiles - Audio file paths
   * @param {string} params.description - Voice description
   * @returns {Promise<Object>} - Voice cloning result
   */
  async cloneVoice(params) {
    try {
      if (!this.apiKey) {
        throw new Error('ElevenLabs API key not configured');
      }

      const {
        name,
        audioFiles,
        description = `Cloned voice: ${name}`,
        labels = {}
      } = params;

      if (!audioFiles || audioFiles.length === 0) {
        throw new Error('Audio files are required for voice cloning');
      }

      logger.info('Cloning voice:', {
        name,
        audioFilesCount: audioFiles.length,
        description
      });

      const formData = new FormData();
      formData.append('name', name);
      formData.append('description', description);
      formData.append('labels', JSON.stringify(labels));

      // Add audio files
      audioFiles.forEach((audioFile, index) => {
        if (fs.existsSync(audioFile)) {
          const audioData = fs.readFileSync(audioFile);
          formData.append('files', audioData, `sample_${index}.wav`);
        }
      });

      const response = await axios.post(
        `${this.baseURL}/voices/add`,
        formData,
        {
          headers: {
            'xi-api-key': this.apiKey,
            'Content-Type': 'multipart/form-data'
          },
          timeout: 120000 // 2 minutes for voice cloning
        }
      );

      logger.info('Voice cloned successfully:', {
        voiceId: response.data.voice_id,
        name
      });

      return {
        success: true,
        voiceId: response.data.voice_id,
        name,
        description
      };

    } catch (error) {
      logger.error('Voice cloning failed:', error.message);
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Generate speech for social media content with optimal settings
   * @param {Object} params - Social TTS parameters
   * @param {string} params.content - Content to convert
   * @param {string} params.platform - Target platform
   * @param {string} params.voiceType - Voice type (professional, casual, energetic)
   * @returns {Promise<Object>} - Social TTS result
   */
  async generateSocialAudio(params) {
    try {
      const {
        content,
        platform = 'general',
        voiceType = 'professional',
        includeIntro = false,
        includeOutro = false
      } = params;

      // Select appropriate voice based on type and platform
      let voiceId = this.defaultVoiceId;
      let voiceSettings = {
        stability: 0.5,
        similarity_boost: 0.8,
        style: 0.0,
        use_speaker_boost: true
      };

      // Platform-specific optimizations
      switch (platform.toLowerCase()) {
      case 'tiktok':
      case 'instagram':
        voiceSettings.style = 0.3; // More expressive for short-form video
        voiceSettings.stability = 0.6;
        break;
      case 'linkedin':
        voiceSettings.stability = 0.7; // More stable for professional content
        voiceSettings.style = 0.1;
        break;
      case 'youtube':
        voiceSettings.similarity_boost = 0.9; // Higher quality for longer content
        break;
      }

      // Voice type adjustments
      switch (voiceType.toLowerCase()) {
      case 'energetic':
        voiceSettings.style = 0.4;
        voiceSettings.stability = 0.4;
        break;
      case 'casual':
        voiceSettings.style = 0.2;
        voiceSettings.stability = 0.5;
        break;
      case 'professional':
        voiceSettings.style = 0.1;
        voiceSettings.stability = 0.7;
        break;
      }

      // Add intro/outro if requested
      let processedContent = content;
      if (includeIntro) {
        processedContent = `Hello everyone! ${processedContent}`;
      }
      if (includeOutro) {
        processedContent += ' Thanks for listening!';
      }

      const result = await this.textToSpeech({
        text: processedContent,
        voiceId,
        voiceSettings,
        outputFormat: 'mp3'
      });

      if (result.success) {
        result.metadata.platform = platform;
        result.metadata.voiceType = voiceType;
        result.metadata.optimizedFor = 'social_media';
      }

      return result;

    } catch (error) {
      logger.error('Social audio generation failed:', error.message);
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Create an audiobook-style narration
   * @param {Object} params - Audiobook parameters
   * @param {string} params.content - Content to narrate
   * @param {string} params.voiceId - Narrator voice ID
   * @param {boolean} params.addChapterMarks - Add chapter markers
   * @returns {Promise<Object>} - Audiobook result
   */
  async createAudiobook(params) {
    try {
      const {
        content,
        voiceId = this.defaultVoiceId,
        addChapterMarks = true,
        chapterBreak = '\n\n---\n\n',
        narratorStyle = 'storytelling'
      } = params;

      // Split content into chapters if chapter marks are requested
      let chapters = [content];
      if (addChapterMarks && content.includes(chapterBreak)) {
        chapters = content.split(chapterBreak);
      }

      const results = {
        chapters: [],
        totalDuration: 0,
        audioFiles: []
      };

      // Audiobook-optimized voice settings
      const voiceSettings = {
        stability: 0.8,  // Very stable for long narration
        similarity_boost: 0.9,  // High quality
        style: narratorStyle === 'storytelling' ? 0.3 : 0.1,
        use_speaker_boost: true
      };

      // Generate audio for each chapter
      for (let i = 0; i < chapters.length; i++) {
        const chapter = chapters[i].trim();
        if (chapter.length === 0) {
          continue;
        }

        logger.info(`Generating audiobook chapter ${i + 1}/${chapters.length}`);

        const chapterResult = await this.textToSpeech({
          text: chapter,
          voiceId,
          voiceSettings,
          outputFormat: 'mp3'
        });

        if (chapterResult.success) {
          results.chapters.push({
            index: i + 1,
            audioFile: chapterResult.audioFile,
            duration: chapterResult.duration,
            fileSize: chapterResult.fileSize
          });
          results.audioFiles.push(chapterResult.filepath);
          results.totalDuration += chapterResult.duration;
        }
      }

      logger.info('Audiobook generation completed:', {
        chapters: results.chapters.length,
        totalDuration: results.totalDuration,
        totalSize: results.chapters.reduce((sum, ch) => sum + ch.fileSize, 0)
      });

      return {
        success: true,
        results,
        metadata: {
          voiceId,
          narratorStyle,
          chaptersCount: results.chapters.length,
          timestamp: new Date().toISOString()
        }
      };

    } catch (error) {
      logger.error('Audiobook creation failed:', error.message);
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Test ElevenLabs connection
   * @returns {Promise<boolean>} - Connection status
   */
  async testConnection() {
    try {
      if (!this.apiKey) {
        return false;
      }

      const response = await axios.get(`${this.baseURL}/voices`, {
        headers: {
          'xi-api-key': this.apiKey
        },
        timeout: 10000
      });

      return response.status === 200 && response.data.voices;
    } catch (error) {
      logger.error('ElevenLabs connection test failed:', error.message);
      return false;
    }
  }

  /**
   * Get user subscription info
   * @returns {Promise<Object>} - Subscription information
   */
  async getUserInfo() {
    try {
      if (!this.apiKey) {
        throw new Error('ElevenLabs API key not configured');
      }

      const response = await axios.get(`${this.baseURL}/user`, {
        headers: {
          'xi-api-key': this.apiKey
        }
      });

      return {
        success: true,
        data: response.data
      };

    } catch (error) {
      logger.error('Failed to get user info:', error.message);
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Estimate audio duration from text length
   * @param {string} text - Text to estimate
   * @returns {number} - Estimated duration in seconds
   */
  estimateAudioDuration(text) {
    // Average speaking rate: ~150 words per minute
    const wordsPerMinute = 150;
    const words = text.split(/\s+/).length;
    const minutes = words / wordsPerMinute;
    return Math.round(minutes * 60);
  }

  /**
   * Get recommended voice for content type
   * @param {string} contentType - Type of content
   * @param {string} audience - Target audience
   * @returns {string} - Recommended voice ID
   */
  getRecommendedVoice(contentType, audience = 'general') {
    // This would ideally fetch from a database or configuration
    // For now, return some common voice IDs based on content type
    const voiceMap = {
      'professional': 'pNInz6obpgDQGcFmaJgB', // Adam
      'casual': 'EXAVITQu4vr4xnSDxMaL',     // Bella
      'energetic': '21m00Tcm4TlvDq8ikWAM',   // Rachel
      'storytelling': 'AZnzlk1XvdvUeBnXmlld', // Domi
      'news': 'pNInz6obpgDQGcFmaJgB',       // Adam
      'educational': 'ErXwobaYiN019PkySvjV'  // Antoni
    };

    return voiceMap[contentType] || this.defaultVoiceId;
  }

  /**
   * Clean up old audio files
   * @param {number} maxAgeHours - Maximum age in hours
   * @returns {Promise<Object>} - Cleanup result
   */
  async cleanupOldFiles(maxAgeHours = 24) {
    try {
      const files = fs.readdirSync(this.outputDir);
      const cutoffTime = Date.now() - (maxAgeHours * 60 * 60 * 1000);
      let deletedCount = 0;
      let totalSize = 0;

      for (const file of files) {
        if (file.startsWith('tts_') && file.endsWith('.mp3')) {
          const filepath = path.join(this.outputDir, file);
          const stats = fs.statSync(filepath);

          if (stats.mtime.getTime() < cutoffTime) {
            totalSize += stats.size;
            fs.unlinkSync(filepath);
            deletedCount++;
          }
        }
      }

      logger.info('Audio file cleanup completed:', {
        deletedCount,
        totalSize,
        maxAgeHours
      });

      return {
        success: true,
        deletedCount,
        totalSize
      };

    } catch (error) {
      logger.error('Audio file cleanup failed:', error.message);
      return {
        success: false,
        error: error.message
      };
    }
  }
}

// Export singleton instance
export default new ElevenLabsService();