const { GoogleGenerativeAI } = require('@google/generative-ai');
const Redis = require('ioredis');
const fs = require('fs').promises;
const path = require('path');
const crypto = require('crypto');
const pino = require('pino');

const logger = pino({ level: 'info' });
const redis = new Redis(process.env.REDIS_URL || 'redis://localhost:6379');
const genAI = new GoogleGenerativeAI(process.env.GOOGLE_AI_STUDIO_API_KEY);

class VideoService {
  constructor() {
    this.model = genAI.getGenerativeModel({ model: 'gemini-pro-vision' });
    this.outDir = path.join(__dirname, '../../generated-videos');
    fs.mkdir(this.outDir, { recursive: true }).catch(() => {});
  }

  async generateVideo(prompt, opts = {}) {
    const id = `v-${Date.now()}-${crypto.randomBytes(4).toString('hex')}`;
    const key = `vid:${crypto.createHash('md5').update(JSON.stringify({ prompt, opts })).digest('hex')}`;
    const cached = await redis.get(key);
    if (cached) return JSON.parse(cached);

    const result = await this.model.generateContent(`Create a ${opts.style || 'cinematic'} video: ${prompt}`);
    const url = result.response?.candidates?.[0]?.content?.parts?.[0]?.fileUri;
    if (!url) throw new Error('No video URL returned');

    const filePath = path.join(this.outDir, `${id}.mp4`);
    await fs.writeFile(filePath, Buffer.from(url)); // stub – replace with real download
    const meta = { id, prompt, url, filePath, created: new Date() };
    await redis.setex(key, 86400, JSON.stringify(meta));
    return meta;
  }
}
module.exports = VideoService;