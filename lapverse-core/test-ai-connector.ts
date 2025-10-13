import axios from 'axios';
import * as path from 'node:path';
import * as fs from 'node:fs';
import * as dotenv from 'dotenv';

function loadEnv() {
  const root = path.resolve(__dirname, '..', '..');
  const local = path.resolve(root, '.env.local');
  const localAlt = path.resolve(__dirname, '.env.local');
  if (fs.existsSync(local)) dotenv.config({ path: local });
  else if (fs.existsSync(localAlt)) dotenv.config({ path: localAlt });
  else dotenv.config();
}

async function testEngine(name: string, url?: string, key?: string) {
  if (!url || !key) {
    console.log(`[skip] ${name}: missing URL or KEY`);
    return false;
  }
  try {
    // Generic JSON echo-style test; adapt as needed per provider
    const resp = await axios.post(url, {
      messages: [{ role: 'user', content: 'ping' }],
      model: process.env[`${name.toUpperCase()}_MODEL`] || 'auto',
      stream: false
    }, {
      headers: {
        Authorization: `Bearer ${key}`,
        'Content-Type': 'application/json'
      },
      timeout: 10000
    });
    const ok = resp.status >= 200 && resp.status < 300;
    console.log(`[ok] ${name}: status=${resp.status}`);
    return ok;
  } catch (err: any) {
    console.log(`[fail] ${name}:`, err?.response?.status || err?.message);
    return false;
  }
}

(async () => {
  loadEnv();
  const qwenOk = await testEngine('qwen', process.env.QWEN_API_URL, process.env.QWEN_API_KEY);
  const kimiOk = await testEngine('kimi', process.env.KIMI_API_URL, process.env.KIMI_API_KEY);
  if (qwenOk && kimiOk) {
    console.log('CONNECTED');
    process.exit(0);
  }
  process.exit((qwenOk || kimiOk) ? 0 : 1);
})();
