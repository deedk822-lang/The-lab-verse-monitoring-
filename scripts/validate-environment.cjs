const fs = require('fs');
const path = require('path');

// List of required keys based on your CI workflow
const REQUIRED_KEYS = [
  'OPENAI_API_KEY',
  'COHERE_API_KEY',
  'GROQ_API_KEY',
  'ANTHROPIC_API_KEY',
  'HUGGINGFACE_TOKEN',
  'GLM4_API_KEY',
  'MISTRAL_API_KEY'
];

console.log("🔍 Starting Environment Validation...");

// 1. Check if .env file exists (created by the previous step)
const envPath = path.join(__dirname, '..', '.env');
if (fs.existsSync(envPath)) {
    console.log("✅ .env file found.");
} else {
    console.warn("⚠️  .env file not found (checking process environment only).");
}

// 2. Validate Variables
let missingKeys = [];

REQUIRED_KEYS.forEach(key => {
    // Check both process.env and if the value is not empty
    if (!process.env[key] || process.env[key].trim() === '') {
        // In CI, secrets might be masked, but they should exist
        missingKeys.push(key);
    } else {
        // Print safely (masked)
        const val = process.env[key];
        const masked = val.substring(0, 3) + '...';
        console.log(`✅ ${key} is present (${masked})`);
    }
});

// 3. Report Results
if (missingKeys.length > 0) {
    console.error("\n❌ FATAL: Missing required environment variables:");
    missingKeys.forEach(key => console.error(`   - ${key}`));
    console.error("\nPlease check your GitHub Repository Secrets and ensure they are mapped in the workflow file.");
    process.exit(1);
}

console.log("\n✅ Environment validation successful! All secrets are mapped correctly.");
process.exit(0);
