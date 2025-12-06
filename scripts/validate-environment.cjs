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
    required: false,
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

  // Optional communication services
  communication: {
    required: false,
    variables: [
      { name: 'TWILIO_ACCOUNT_SID', provider: 'Twilio', url: 'https://twilio.com', optional: true },
      { name: 'TWILIO_AUTH_TOKEN', provider: 'Twilio', url: 'https://twilio.com', optional: true }
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

    // Display warnings
    if (this.warnings.length > 0) {
      this.log('\n⚠ Optional Services (Not Configured):', 'yellow');
      this.warnings.forEach(warning => {
        this.log(`  ${warning.variable} (${warning.provider})`, 'yellow');
        this.log(`    Get key at: ${warning.url}`, 'yellow');
      });
    }

    // Display errors
    if (this.errors.length > 0) {
      this.log('\n✗ Configuration Errors:', 'red');
      this.errors.forEach(error => {
        if (Array.isArray(error.providers)) {
          this.log(`  ${error.variable}: ${error.message}`, 'red');
          error.providers.forEach(provider => {
            if (typeof provider === 'string') {
              this.log(`    - ${provider}`, 'red');
            } else {
              this.log(`    - ${provider.name} (${provider.key})`, 'red');
              this.log(`      Get key at: ${provider.url}`, 'red');
            }
          });
        } else {
          this.log(`  ${error.variable}: ${error.message}`, 'red');
          if (error.url) {
            this.log(`    Get key at: ${error.url}`, 'red');
          }
        }
      });
      this.log('', 'reset');
      process.exit(1);
    }

    // Display configured
    if (this.configured.length > 0) {
      this.log('✓ Configured Services:', 'green');
      this.configured.forEach(item => {
        this.log(`  ${item.variable}: ${item.value}`, 'green');
      });
    }

    this.log('\n✓ Environment validation passed!', 'green');
  }
}

// Run validation
const validator = new EnvironmentValidator();
validator.validate();
