 main
import { config } from 'dotenv';
import { fileURLToPath } from 'url';
import { dirname, resolve } from 'path';

// ES module __dirname workaround
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Load .env.local from parent directory
config({ path: resolve(__dirname, '../.env.local') });

import { connectAI } from './src/ai/Connector.js';
import { FinOpsTagger } from './src/cost/FinOpsTagger.js';

async function testConnection() {
  console.log('Testing AI Connector...');
  console.log('DASHSCOPE_API_KEY:', process.env.DASHSCOPE_API_KEY ? '✓ Set' : '✗ Missing');
  console.log('MOONSHOT_API_KEY:', process.env.MOONSHOT_API_KEY ? '✓ Set' : '✗ Missing');
  
  const finops = new FinOpsTagger();
  const prompt = 'Analyze this test: win_rate=0.07, cost_per_comp=0.042. Flag anomalies.';
  
  try {
    const result = await connectAI(prompt, finops, {
      artifactId: 'test-' + Date.now(),
      tenantId: 'test-tenant'
    });
    
    console.log('\n✓ CONNECTED - AI Response:');
    console.log('Qwen Analysis:', result.qwen);
    console.log('Kimi Response:', result.kimi);
    console.log('\nTest successful! Both AI engines are working.');
  } catch (error: any) {
    console.error('\n✗ Connection failed:', error.message);
    if (error.response) {
      console.error('API Response:', error.response.data);
    }
    process.exit(1);
  }
}

testConnection();

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
 cursor/the-lap-verse-core-service-polish-ae35
