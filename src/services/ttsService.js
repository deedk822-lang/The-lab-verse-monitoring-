const ElevenLabs = require('elevenlabs-node');
const Redis = require('ioredis');
const fs = require('fs').promises;
const path = require('path');
const crypto = require('crypto');
const pino = require('pino');

const logger = pino({ level: 'info' });
const redis = new Redis(process.env.REDIS_URL || 'redis://localhost:6379');
const eleven = new ElevenLabs({ apiKey: process.env.ELEVEN_LABS_API_KEY });

class TTSService {
  constructor() {
    this.outDir = path.join(__dirname, '../../generated-audio');
    fs.mkdir(this.outDir, { recursive: true }).catch(() => {});
  }

  async generateSpeech(text, opts) {
    const key = `tts:${crypto.createHash('md5').update(JSON.stringify({ text, opts })).digest('hex')}`;
    const cached = await redis.getBuffer(key);
    if (cached) return { audioBuffer: cached, cached: true };

    const audioStream = await eleven.textToSpeechStream(text, {
      voiceId: opts.voiceId || '21m00Tcm4TlvDq8ikWAM',
      modelId: 'eleven_multilingual_v2',
      voiceSettings: { stability: opts.stability || 0.75, similarityBoost: opts.similarityBoost || 0.75 }
    });
    const chunks = [];
    for await (const chunk of audioStream) chunks.push(chunk);
    const buffer = Buffer.concat(chunks);

    await redis.setex(key, 3600, buffer);
    return { audioBuffer: buffer, cached: false };
  }
}
module.exports = TTSService;