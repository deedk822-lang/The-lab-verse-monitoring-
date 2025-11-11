import { textToSpeech } from 'elevenlabs-node';
import Redis from 'ioredis';
import fs from 'fs/promises';
import path from 'path';
import crypto from 'crypto';
import pino from 'pino';
import { fileURLToPath } from 'url';
import { dirname } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

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
    if (cached) {
      return { audioBuffer: cached, cached: true };
    }

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
export default TTSService;