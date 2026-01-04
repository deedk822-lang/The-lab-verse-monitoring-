/**
 * Secure Configuration Module
 * NO DEFAULT SECRETS - Fail fast if configuration is missing
 */

class ConfigurationError extends Error {
  constructor(message) {
    super(message);
    this.name = 'ConfigurationError';
  }
}

/**
 * Validates required environment variable exists
 * @param {string} varName - Environment variable name
 * @param {string} description - Human-readable description
 * @returns {string} The environment variable value
 * @throws {ConfigurationError} If variable is missing
 */
function requireEnv(varName, description) {
  const value = process.env[varName];

  if (!value || value.trim() === '') {
    throw new ConfigurationError(
      `Missing required environment variable: ${varName}\n` +
      `Description: ${description}\n` +
      `Please set this in your .env file or environment.`
    );
  }

  return value.trim();
}

/**
 * Gets optional environment variable with validation
 * @param {string} varName - Environment variable name
 * @param {string} defaultValue - Default value if not set
 * @param {Function} validator - Optional validation function
 * @returns {string} The environment variable value or default
 */
function getEnv(varName, defaultValue, validator = null) {
  const value = process.env[varName] || defaultValue;

  if (validator && !validator(value)) {
    throw new ConfigurationError(
      `Invalid value for ${varName}: ${value}`
    );
  }

  return value;
}

/**
 * Validates API key format
 */
function isValidApiKey(key) {
  return key && key.length >= 32 && !key.includes('default') && !key.includes('change-me');
}

/**
 * Validates URL format
 */
function isValidUrl(url) {
  try {
    new URL(url);
    return true;
  } catch {
    return false;
  }
}

/**
 * Application Configuration
 */
const config = {
  // Environment
  environment: getEnv('NODE_ENV', 'development'),

  // API Keys - REQUIRED, NO DEFAULTS
  apiKeys: {
    openai: requireEnv('OPENAI_API_KEY', 'OpenAI API key for GPT models'),
    anthropic: requireEnv('ANTHROPIC_API_KEY', 'Anthropic API key for Claude models'),
    contentCreator: requireEnv('CONTENT_CREATOR_API_KEY', 'Internal API key for content creator service'),
  },

  // Service URLs
  services: {
    orchestrator: getEnv(
      'ORCHESTRATOR_URL',
      'http://localhost:8081',
      isValidUrl
    ),
    database: requireEnv('DATABASE_URL', 'PostgreSQL connection string'),
    redis: getEnv('REDIS_URL', 'redis://localhost:6379', isValidUrl),
  },

  // Server Configuration
  server: {
    port: parseInt(getEnv('PORT', '3001'), 10),
    host: getEnv('HOSTNAME', '0.0.0.0'),
    timeout: parseInt(getEnv('SERVER_TIMEOUT', '30000'), 10),
  },

  // Security
  security: {
    jwtSecret: requireEnv('JWT_SECRET', 'JWT signing secret (min 32 chars)'),
    corsOrigins: getEnv('CORS_ORIGINS', '*').split(','),
    rateLimitWindowMs: parseInt(getEnv('RATE_LIMIT_WINDOW', '60000'), 10),
    rateLimitMaxRequests: parseInt(getEnv('RATE_LIMIT_MAX', '100'), 10),
  },

  // Logging
  logging: {
    level: getEnv('LOG_LEVEL', 'info'),
    format: getEnv('LOG_FORMAT', 'json'),
  },

  // AI Model Configuration
  models: {
    default: getEnv('DEFAULT_MODEL', 'gpt-4'),
    maxTokens: parseInt(getEnv('MAX_TOKENS', '2000'), 10),
    temperature: parseFloat(getEnv('TEMPERATURE', '0.7')),
  },

  // Feature Flags
  features: {
    webSearch: getEnv('FEATURE_WEB_SEARCH', 'true') === 'true',
    analytics: getEnv('FEATURE_ANALYTICS', 'true') === 'true',
    monitoring: getEnv('FEATURE_MONITORING', 'true') === 'true',
  },
};

/**
 * Validates entire configuration on startup
 * @throws {ConfigurationError} If any validation fails
 */
function validateConfig() {
  const errors = [];

  // Validate API keys
  if (!isValidApiKey(config.apiKeys.openai)) {
    errors.push('OPENAI_API_KEY must be at least 32 characters and not contain "default" or "change-me"');
  }

  if (!isValidApiKey(config.apiKeys.anthropic)) {
    errors.push('ANTHROPIC_API_KEY must be at least 32 characters and not contain "default" or "change-me"');
  }

  if (!isValidApiKey(config.apiKeys.contentCreator)) {
    errors.push('CONTENT_CREATOR_API_KEY must be at least 32 characters and not contain "default" or "change-me"');
  }

  // Validate JWT secret
  if (config.security.jwtSecret.length < 32) {
    errors.push('JWT_SECRET must be at least 32 characters');
  }

  // Validate numeric values
  if (config.server.port < 1 || config.server.port > 65535) {
    errors.push('PORT must be between 1 and 65535');
  }

  if (config.models.temperature < 0 || config.models.temperature > 2) {
    errors.push('TEMPERATURE must be between 0 and 2');
  }

  if (errors.length > 0) {
    throw new ConfigurationError(
      'Configuration validation failed:\n' + errors.map(e => `  - ${e}`).join('\n')
    );
  }
}

// Validate on module load
try {
  validateConfig();
  console.log('✓ Configuration validated successfully');

  // Mask sensitive values in logs
  console.log('Configuration loaded:', {
    environment: config.environment,
    server: config.server,
    services: {
      orchestrator: config.services.orchestrator,
      database: config.services.database.replace(/:[^:]*@/, ':****@'), // Mask password
      redis: config.services.redis,
    },
    features: config.features,
  });
} catch (error) {
  console.error('❌ Configuration Error:', error.message);
  console.error('\nPlease check your .env file or environment variables.');
  console.error('See .env.example for required configuration.\n');
  process.exit(1);
}

module.exports = config;