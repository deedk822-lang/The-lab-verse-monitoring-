# Groq Integration Guide

✅ **Status**: Groq has been successfully added to the multi-provider fallback chain!

## What Was Added

### 1. Groq SDK Installation
```bash
npm install groq-sdk
```

### 2. Native Groq Provider (`src/providers/groqProvider.js`)
A standalone provider using Groq's native SDK for maximum performance:
- **Models Available**: Llama 3.1 70B, Llama 3.1 8B, Mixtral 8x7B, Gemma 2 9B
- **Features**: Native streaming, sub-100ms token latency
- **Lazy Loading**: Only initializes when API key is present

### 3. Multi-Provider Fallback Chain (`src/providers/multiProviderFallback.js`)
Unified fallback system that tries providers in order:
1. **OpenAI** (GPT-4)
2. **Groq** (Llama 3.1 70B) ⚡ **NEW**
3. **Perplexity** (Sonar)
4. **Gemini** (Pro)

### 4. EVI Integration Updated
Updated `src/integrations/eviIntegration.js` to include Groq in the provider list.

### 5. Vercel AI SDK Integration
Groq is also available via OpenAI-compatible endpoint in `src/config/providers.js`:
- Provider name: `groq-llama`
- Category: `anthropic-fallback`
- Priority: 6

## Quick Start

### 1. Get Your API Key
1. Visit [console.groq.com/keys](https://console.groq.com/keys)
2. Create a new API key
3. Copy the value (starts with `gsk_...`)

### 2. Configure Environment

**Local Development:**
```bash
export GROQ_API_KEY=gsk_your_key_here
```

**Vercel Deployment:**
```bash
# Add in Vercel Dashboard → Settings → Environment Variables
GROQ_API_KEY=gsk_your_key_here
```

**`.env` File:**
```env
GROQ_API_KEY=gsk_your_key_here
```

### 3. Test the Integration
```bash
npm run test:ai
```

This will test all providers and show which ones are configured and working.

## Usage Examples

### Option 1: Multi-Provider Fallback (Recommended)
```javascript
import { multiProviderGenerate } from './src/providers/multiProviderFallback.js';

// Automatically tries providers in order until one succeeds
const result = await multiProviderGenerate(
  'Write a short poem about AI',
  { 
    temperature: 0.7, 
    max_tokens: 200 
  }
);

console.log(`Provider used: ${result.provider}`);
console.log(`Response: ${result.text}`);
```

### Option 2: Direct Groq Access
```javascript
import { generateGroq, GROQ_MODELS } from './src/providers/groqProvider.js';

const response = await generateGroq({
  model: GROQ_MODELS.LLAMA_70B,
  messages: [
    { role: 'user', content: 'Hello!' }
  ],
  temperature: 0.7,
  max_tokens: 100
});

console.log(response);
```

### Option 3: Streaming with Groq
```javascript
import { streamGroq } from './src/providers/groqProvider.js';

for await (const chunk of streamGroq({
  messages: [{ role: 'user', content: 'Count to 10' }],
  max_tokens: 100
})) {
  process.stdout.write(chunk);
}
```

### Option 4: Via EVI Integration
```javascript
import { evi } from './src/integrations/eviIntegration.js';

// Uses intelligent fallback including Groq
const result = await evi.multiProviderGenerate(
  'Generate a product description',
  { maxTokens: 500 }
);

console.log(`Used: ${result.providerUsed}`);
console.log(`Fallback attempts: ${result.fallbackAttempts}`);
```

## Available Models

| Model | ID | Best For |
|-------|----|---------| 
| **Llama 3.1 70B** | `llama-3.1-70b-versatile` | General purpose, high quality |
| **Llama 3.1 8B** | `llama-3.1-8b-instant` | Fast responses, simple tasks |
| **Mixtral 8x7B** | `mixtral-8x7b-32768` | Long context (32k tokens) |
| **Gemma 2 9B** | `gemma2-9b-it` | Instruction following |

## Architecture

### Fallback Flow
```
Request → OpenAI
          ↓ (fails)
          Groq ⚡
          ↓ (fails)
          Perplexity
          ↓ (fails)
          Gemini
          ↓ (fails)
          Error
```

### Two Integration Modes

1. **Native Groq SDK** (new)
   - Direct access to Groq API
   - Custom message formatting
   - Located in `src/providers/groqProvider.js`

2. **Vercel AI SDK** (existing)
   - Uses OpenAI-compatible endpoint
   - Works with existing `streamText` infrastructure
   - Located in `src/config/providers.js`

## Testing

### Run All Provider Tests
```bash
npm run test:ai
```

### Expected Output (with API key configured)
```
📋 Test 3: Testing All Providers
------------------------------------------------------------
┌──────────┬──────────────┬─────────────────────────┬────────────┬─────────┐
│ (index)  │ status       │ response                │ duration   │ working │
├──────────┼──────────────┼─────────────────────────┼────────────┼─────────┤
│ Groq     │ '✅ Success' │ 'Hello from Llama 3.1'  │ '234ms'    │ true    │
└──────────┴──────────────┴─────────────────────────┴────────────┴─────────┘
```

## Benefits

✅ **Fast**: Sub-100ms token latency  
✅ **Free**: 30 requests/minute on free tier  
✅ **Fallback**: Automatic failover to other providers  
✅ **Flexible**: Multiple integration options  
✅ **Production-Ready**: Lazy loading, error handling, streaming support  

## Rate Limits

**Free Tier:**
- 30 requests/minute
- 14,400 requests/day

**Tips:**
- Use for real-time applications where speed matters
- Falls back to other providers when rate limited
- Consider caching responses for repeated queries

## Troubleshooting

### "GROQ_API_KEY environment variable is not set"
**Solution:** Export the API key or add to `.env` file

### "All providers exhausted"
**Solution:** At least one provider needs to be configured. Run `npm run test:ai` to see which providers are available.

### Rate limit errors
**Solution:** The fallback chain will automatically try the next provider. Consider implementing request queuing for high-volume applications.

## Files Modified

1. ✅ `package.json` - Added `groq-sdk` dependency and `test:ai` script
2. ✅ `src/providers/groqProvider.js` - New native Groq provider
3. ✅ `src/providers/multiProviderFallback.js` - New unified fallback system
4. ✅ `src/integrations/eviIntegration.js` - Added Groq to provider list
5. ✅ `test-groq-integration.js` - Comprehensive test suite

## Next Steps

1. **Deploy**: Add `GROQ_API_KEY` to Vercel environment variables
2. **Monitor**: Track which providers are being used most
3. **Optimize**: Adjust provider order based on your use case
4. **Scale**: Consider implementing request queuing for rate limit management

## Support

- Groq Documentation: https://console.groq.com/docs
- Groq Models: https://console.groq.com/docs/models
- API Keys: https://console.groq.com/keys

---

**Status**: ✅ Complete - Groq is now a full citizen in your AI provider ecosystem!
