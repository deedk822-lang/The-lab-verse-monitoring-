import dotenv from 'dotenv';
dotenv.config({ path: '.env.local' });

const assert = (v, m) => {
  if (!v) {
    throw new Error(`ENV missing: ${m}`);
  }
};

assert(process.env.JWT_SECRET, 'JWT_SECRET');
assert(process.env.GOOGLE_AI_STUDIO_API_KEY, 'GOOGLE_AI_STUDIO_API_KEY');
assert(process.env.ELEVEN_LABS_API_KEY, 'ELEVEN_LABS_API_KEY');
assert(process.env.SLACK_WEBHOOK_URL, 'SLACK_WEBHOOK_URL');

export default {
  PORT: process.env.PORT || 3000,
  REDIS_URL: process.env.REDIS_URL || 'redis://localhost:6379',
  JWT_SECRET: process.env.JWT_SECRET,
  GOOGLE_AI_STUDIO_API_KEY: process.env.GOOGLE_AI_STUDIO_API_KEY,
  ELEVEN_LABS_API_KEY: process.env.ELEVEN_LABS_API_KEY,
  SLACK_WEBHOOK_URL: process.env.SLACK_WEBHOOK_URL
};