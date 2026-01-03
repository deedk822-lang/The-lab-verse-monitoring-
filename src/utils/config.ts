// Validate all required environment variables at startup
const requiredEnvVars = [
  'NEXT_PUBLIC_API_ENDPOINT',
  'NEXT_PUBLIC_EVENT_DATE'
];

export function validateEnvironment() {
  const missing = requiredEnvVars.filter(v => !process.env[v]);

  if (missing.length > 0) {
    console.error(`Missing required env vars: ${missing.join(', ')}`);
    throw new Error('Configuration validation failed');
  }
}

// Safe getter with fallback
export function getEnvVar(key: string, fallback?: string): string {
  const value = process.env[key] || fallback;
  if (!value) {
    throw new Error(`Environment variable ${key} is required but not set`);
  }
  return value;
}
