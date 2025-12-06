// scripts/validate-environment.cjs

const requiredSecrets = [
  'OPENAI_API_KEY',
  'COHERE_API_KEY',
  'GROQ_API_KEY',
  'ANTHROPIC_API_KEY',
  'HUGGINGFACE_TOKEN',
  'GLM4_API_KEY',
  'MISTRAL_API_KEY',
];

let missingSecrets = [];

for (const secret of requiredSecrets) {
  if (!process.env[secret]) {
    missingSecrets.push(secret);
  }
}

if (missingSecrets.length > 0) {
  console.error(`❌ Missing required environment variables: ${missingSecrets.join(', ')}`);
  process.exit(1);
}

console.log('✅ All required environment variables are set.');
process.exit(0);
