const { textToSpeech, getVoices } = require('elevenlabs-node');
const Redis = require('ioredis');
const fs = require('fs').promises;
const path = require('path');
const crypto = require('crypto');
const pino = require('pino');

const logger = pino({ level: 'info' });
const redis = new Redis(process.env.REDIS_URL || 'redis://localhost:6379');

class TTSService {
  constructor() {
    this.outDir = path.join(__dirname, '../../generated-audio');
    fs.mkdir(this.outDir, { recursive: true }).catch(() => {});
  }

  async generateSpeech(text, opts) {
    const key = `tts:${crypto.createHash('md5').update(JSON.stringify({ text, opts })).digest('hex')}`;
    const cached = await redis.getBuffer(key);
    if (cached) return { audioBuffer: cached, cached: true };

    try {
      const audioBuffer = await textToSpeech(process.env.ELEVEN_LABS_API_KEY, text, {
        voiceId: opts.voiceId || '21m00Tcm4TlvDq8ikWAM',
        modelId: 'eleven_multilingual_v2',
        voiceSettings: { stability: opts.stability || 0.75, similarityBoost: opts.similarityBoost || 0.75 }
      });

      await redis.setex(key, 3600, audioBuffer);
      return { audioBuffer, cached: false };
    } catch (error) {
      logger.error('TTS generation failed:', error);
      throw new Error('TTS generation failed');
    }
  }
}
module.exports = TTSService;