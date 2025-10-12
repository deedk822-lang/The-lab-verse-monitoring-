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
