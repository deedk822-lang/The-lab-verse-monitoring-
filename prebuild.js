const requiredEnvVar = 'NEXT_PUBLIC_EVENT_DATE';

if (!process.env[requiredEnvVar]) {
  console.error(`Error: Required environment variable "${requiredEnvVar}" is not set.`);
  console.error('This variable is necessary for the application to build correctly.');
  console.error('Please ensure it is defined in your Vercel project settings or .env.local file.');
  process.exit(1);
}

console.log(`Successfully validated the presence of "${requiredEnvVar}".`);
