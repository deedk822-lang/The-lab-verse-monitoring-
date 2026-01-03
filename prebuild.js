const required = ["VERCEL_TOKEN", "DATABASE_URL", "METRICS_API_TOKEN"];

const missing = required.filter(k => !process.env[k]);

if (missing.length > 0) {
  console.error("BUILD FAILED: Missing critical server-side environment variables.");
  console.error(`The following variables were not found: ${missing.join(', ')}.`);
  console.error("Please ensure these are set in your Vercel project environment variables.");
  process.exit(1);
}

console.log("Pre-build checks passed: All critical environment variables are present.");
