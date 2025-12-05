#!/usr/bin/env node

/**
 * Environment Variable Validation Script
 * Validates that required environment variables are set and provides helpful error messages
 */

const fs = require('fs');
const path = require('path');

// ANSI color codes
const colors = {
  reset: '\x1b[0m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m'
};

// Environment variable configuration
const envConfig = {
  // At least ONE AI provider is required
  aiProviders: {
    required: false, // Not all required, but at least one
    variables: [
      { name: 'COHERE_API_KEY', provider: 'Cohere', url: 'https://cohere.com' },
      { name: 'GROQ_API_KEY', provider: 'Groq', url: 'https://groq.com' },
      { name: 'OPENAI_API_KEY', provider: 'OpenAI', url: 'https://openai.com' },
      { name: 'ANTHROPIC_API_KEY', provider: 'Anthropic', url: 'https://anthropic.com' },
      { name: 'HUGGINGFACE_TOKEN', provider: 'HuggingFace', url: 'https://huggingface.co' }
    ]
  },

  // Optional AI providers
  optionalAI: {
    required: false,
    variables: [
      { name: 'GLM4_API_KEY', provider: 'Zhipu AI GLM-4', url: 'https://open.bigmodel.cn', optional: true },
      { name: 'GOOGLE_AI_API_KEY', provider: 'Google AI', url: 'https://ai.google.dev', optional: true },
      { name: 'MISTRAL_API_KEY', provider: 'Mistral AI', url: 'https://mistral.ai', optional: true }
    ]
  },

  // Communication services
  communication: {
    required: false,
    variables: [
      { name: 'TWILIO_ACCOUNT_SID', provider: 'Twilio', url: 'https://twilio.com' },
      { name: 'TWILIO_AUTH_TOKEN', provider: 'Twilio', url: 'https://twilio.com' }
    ]
  },

  // Social media
  social: {
    required: false,
    variables: [
      { name: 'AYRSHARE_API_KEY', provider: 'Ayrshare', url: 'https://ayrshare.com', optional: true },
      { name: 'SOCIALPILOT_API_KEY', provider: 'SocialPilot', url: 'https://socialpilot.co', optional: true }
    ]
  },

  // Image generation
  images: {
    required: false,
    variables: [
      { name: 'STABILITY_API_KEY', provider: 'Stability AI', url: 'https://stability.ai', optional: true },
      { name: 'REPLICATE_API_TOKEN', provider: 'Replicate', url: 'https://replicate.com', optional: true }
    ]
  }
};

class EnvironmentValidator {
  constructor() {
    this.errors = [];
    this.warnings = [];
    this.configured = [];
  }

  log(message, color = 'reset') {
    console.log(`${colors[color]}${message}${colors.reset}`);
  }

  validateVariable(varName, config = {}) {
    const value = process.env[varName];
    const { provider, url, optional } = config;

    if (!value || value.trim() === '' || value.includes('your_') || value.includes('_here')) {
      if (optional) {
        this.warnings.push({
          variable: varName,
          provider,
          url,
          message: `Optional: ${varName} not configured`
        });
        return false;
      } else {
        this.errors.push({
          variable: varName,
          provider,
          url,
          message: `Required: ${varName} is not set or invalid`
        });
        return false;
      }
    }

    this.configured.push({
      variable: varName,
      provider,
      value: value.substring(0, 10) + '...'
    });
    return true;
  }

  validateGroup(groupName, group) {
    const results = group.variables.map(varConfig =>
      this.validateVariable(varConfig.name, varConfig)
    );

    // If group requires at least one, check that
    if (group.required && !results.some(r => r)) {
      this.errors.push({
        variable: groupName,
        message: `At least one ${groupName} provider must be configured`,
        providers: group.variables.map(v => `${v.provider} (${v.name})`).join(', ')
      });
      return false;
    }

    // For AI providers, we need at least one
    if (groupName === 'aiProviders' && !results.some(r => r)) {
      this.errors.push({
        variable: 'AI_PROVIDER',
        message: 'At least one AI provider must be configured for the system to work',
        providers: group.variables.map(v => ({
          name: v.provider,
          key: v.name,
          url: v.url
        }))
      });
      return false;
    }

    return true;
  }

  validate() {
    this.log('\n================================', 'blue');
    this.log('ENVIRONMENT VALIDATION', 'blue');
    this.log('================================\n', 'blue');

    // Validate each group
    for (const [groupName, group] of Object.entries(envConfig)) {
      this.validateGroup(groupName, group);
    }

    // Display results
    if (this.configured.length > 0) {
      this.log('\n✓ Configured Services:', 'green');
      this.configured.forEach(({ variable, provider, value }) => {
        this.log(`  ${variable}: ${value}`, 'green');
      });
    }

    if (this.warnings.length > 0) {
      this.log('\n⚠ Optional Services (Not Configured):', 'yellow');
      this.warnings.forEach(({ variable, provider, url }) => {
        this.log(`  ${variable} (${provider})`, 'yellow');
        if (url) {
          this.log(`    Get key at: ${url}`, 'yellow');
        }
      });
    }

    if (this.errors.length > 0) {
      this.log('\n✗ Configuration Errors:', 'red');
      this.errors.forEach((error) => {
        if (error.providers && Array.isArray(error.providers)) {
          this.log(`  ${error.message}`, 'red');
          error.providers.forEach(p => {
            if (typeof p === 'object') {
              this.log(`    - ${p.name} (${p.key})`, 'red');
              this.log(`      Get key at: ${p.url}`, 'red');
            } else {
              this.log(`    - ${p}`, 'red');
            }
          });
        } else {
          this.log(`  ${error.variable}: ${error.message}`, 'red');
          if (error.url) {
            this.log(`    Get key at: ${error.url}`, 'red');
          }
        }
      });

      this.log('\n================================', 'red');
      this.log('VALIDATION FAILED', 'red');
      this.log('================================\n', 'red');

      // Provide helpful instructions
      this.log('To fix these errors:', 'yellow');
      this.log('1. Copy .env.example to .env: cp .env.example .env', 'yellow');
      this.log('2. Edit .env and add your API keys', 'yellow');
      this.log('3. At minimum, configure ONE AI provider (Cohere recommended)', 'yellow');
      this.log('4. Run this script again to verify\n', 'yellow');

      if (process.env.VERCEL) {
        this.log('VERCEL DEPLOYMENT:', 'blue');
        this.log('Configure secrets in Vercel dashboard:', 'yellow');
        this.log('  https://vercel.com/dashboard > Your Project > Settings > Environment Variables\n', 'yellow');
      }

      return false;
    }

    this.log('\n================================', 'green');
    this.log('✓ VALIDATION PASSED', 'green');
    this.log('================================\n', 'green');

    // Show what's working
    const aiProviders = this.configured.filter(c =>
      ['COHERE_API_KEY', 'GROQ_API_KEY', 'OPENAI_API_KEY', 'ANTHROPIC_API_KEY', 'HUGGINGFACE_TOKEN'].includes(c.variable)
    );

    if (aiProviders.length > 0) {
      this.log(`AI Providers Available: ${aiProviders.length}`, 'green');
    }

    const optional = this.configured.filter(c =>
      !['COHERE_API_KEY', 'GROQ_API_KEY', 'OPENAI_API_KEY', 'ANTHROPIC_API_KEY', 'HUGGINGFACE_TOKEN'].includes(c.variable)
    );

    if (optional.length > 0) {
      this.log(`Additional Services: ${optional.length}`, 'green');
    }

    this.log('');
    return true;
  }

  generateReport() {
    return {
      timestamp: new Date().toISOString(),
      configured: this.configured.length,
      warnings: this.warnings.length,
      errors: this.errors.length,
      valid: this.errors.length === 0,
      details: {
        configured: this.configured,
        warnings: this.warnings,
        errors: this.errors
      }
    };
  }
}

// Run validation
function main() {
  const validator = new EnvironmentValidator();
  const isValid = validator.validate();

  // Generate report file
  const report = validator.generateReport();
  const reportPath = path.join(process.cwd(), 'env-validation-report.json');
  fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));

  console.log(`Report saved to: ${reportPath}\n`);

  // Exit with appropriate code
  process.exit(isValid ? 0 : 1);
}

if (require.main === module) {
  main();
}

module.exports = { EnvironmentValidator };