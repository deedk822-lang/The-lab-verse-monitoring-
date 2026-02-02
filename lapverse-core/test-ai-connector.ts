import { config } from 'dotenv';
import { fileURLToPath } from 'url';
import { dirname, resolve } from 'path';
import axios from 'axios';
import * as path from 'node:path';
import * as fs from 'node:fs';

// ES module __dirname workaround
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Load environment variables
function loadEnv() {
  const root = resolve(__dirname, '..');
  const local = resolve(root, '.env.local');
  const localAlt = resolve(__dirname, '.env.local');
  if (fs.existsSync(local)) config({ path: local });
  else if (fs.existsSync(localAlt)) config({ path: localAlt });
  else config();
}

import { connectAI } from './src/ai/Connector.js';
import { FinOpsTagger } from './src/cost/FinOpsTagger.js';

async function testEngine(name: string, url?: string, key?: string) {
  if (!url || !key) {
    console.log(`[skip] ${name}: missing URL or KEY`);
    return false;
  }
  try {
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

async function runTests() {
  loadEnv();
  console.log('Testing AI Connector...');

  const qwenOk = await testEngine('qwen', process.env.QWEN_API_URL, process.env.QWEN_API_KEY);
  const kimiOk = await testEngine('kimi', process.env.KIMI_API_URL, process.env.KIMI_API_KEY);

  if (qwenOk || kimiOk) {
    console.log('\n✓ AI Engines responsive.');
  } else {
    console.warn('\n⚠️  No AI engines responsive, but continuing integration test...');
  }

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
    console.log('\nTest successful! AI connectivity layer is working.');
    process.exit(0);
  } catch (error: any) {
    console.error('\n✗ Integration test failed:', error.message);
    process.exit(1);
  }
}

runTests();
