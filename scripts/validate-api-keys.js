#!/usr/bin/env node

// API Key validation script for CI environment
const apiKeys = {
  'OpenAI': process.env.OPENAI_API_KEY,
  'Anthropic': process.env.ANTHROPIC_API_KEY,
  'Perplexity': process.env.PERPLEXITY_API_KEY,
  'Mistral': process.env.MISTRAL_API_KEY,
  'Groq': process.env.GROQ_API_KEY,
  'Gemini': process.env.GEMINI_API_KEY,
  'LocalAI': process.env.LOCALAI_API_KEY
};

console.log('🔍 API Key Validation Results:');
console.log('================================');

let availableCount = 0;
let totalCount = Object.keys(apiKeys).length;

// Detailed validation with key format checking
const keyValidation = {
  'OpenAI': (key) => key && key.startsWith('sk-') && key.length > 40,
  'Anthropic': (key) => key && key.startsWith('sk-ant-') && key.length > 40,
  'Perplexity': (key) => key && key.startsWith('pplx-') && key.length > 30,
  'Mistral': (key) => key && key.length > 20,
  'Groq': (key) => key && key.startsWith('gsk_') && key.length > 40,
  'Gemini': (key) => key && key.length > 30,
  'LocalAI': (key) => key && key.length > 0
};

Object.entries(apiKeys).forEach(([provider, key]) => {
  const isValid = keyValidation[provider] ? keyValidation[provider](key) : !!key;
  const status = isValid ? '✅ Available & Valid' : key ? '⚠️ Present but Invalid' : '❌ Missing';
  const keyInfo = key ? `(${key.substring(0, 8)}...)` : '(not configured)';
  
  console.log(`${provider.padEnd(12)}: ${status} ${keyInfo}`);
  
  if (isValid) availableCount++;
});

console.log('================================');
console.log(`📊 Summary: ${availableCount}/${totalCount} providers configured`);

// Fallback chain status
console.log('\n🔗 Fallback Chain Status:');
console.log('================================');

const openaiAvailable = keyValidation['OpenAI'](apiKeys['OpenAI']);
const perplexityAvailable = keyValidation['Perplexity'](apiKeys['Perplexity']);
const anthropicAvailable = keyValidation['Anthropic'](apiKeys['Anthropic']);
const mistralAvailable = keyValidation['Mistral'](apiKeys['Mistral']);
const geminiAvailable = keyValidation['Gemini'](apiKeys['Gemini']);
const groqAvailable = keyValidation['Groq'](apiKeys['Groq']);

console.log(`OpenAI Chain:    ${openaiAvailable ? '✅ GPT-4' : '❌ GPT-4'} → ${perplexityAvailable ? '✅ Perplexity' : '❌ Perplexity'}`);
console.log(`Anthropic Chain: ${anthropicAvailable ? '✅ Claude' : '❌ Claude'} → ${mistralAvailable ? '✅ Mistral' : '❌ Mistral'} → ${geminiAvailable ? '✅ Gemini' : '❌ Gemini'} → ${groqAvailable ? '✅ Groq' : '❌ Groq'}`);

// Exit with appropriate code
if (availableCount === 0) {
  console.error('\n❌ CRITICAL: No API keys available! CI will fail.');
  console.error('Please check your GitHub repository secrets configuration.');
  process.exit(1);
} else if (availableCount < 2) {
  console.warn('\n⚠️  WARNING: Limited provider options available');
  console.warn('Consider adding more API keys for better fallback coverage.');
  process.exit(0);
} else {
  console.log('\n✅ SUCCESS: Multiple providers available for robust fallback system');
  console.log(`🎯 Fallback coverage: ${availableCount > 3 ? 'Excellent' : availableCount > 1 ? 'Good' : 'Minimal'}`);
  process.exit(0);
}