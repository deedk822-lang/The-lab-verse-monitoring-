import * as Sentry from '@sentry/node';
import * as Tracing from '@sentry/tracing';

export function initializeSentry(app) {
if (!process.env.SENTRY_DSN) {
console.log('⚠️ Sentry DSN not configured');
return;
}

Sentry.init({
dsn: process.env.SENTRY_DSN,
environment: process.env.NODE_ENV || 'production',
release: process.env.npm_package_version,

// Performance Monitoring
tracesSampleRate: 0.1, // 10% of transactions

// Integrations
integrations: [
new Sentry.Integrations.Http({ tracing: true }),
new Tracing.Integrations.Express({ app }),
new Tracing.Integrations.Postgres(),
new Tracing.Integrations.Mongo(),
],

// Filter sensitive data
beforeSend(event, hint) {
// Remove sensitive headers
if (event.request?.headers) {
delete event.request.headers['authorization'];
delete event.request.headers['cookie'];
}

// Remove API keys from URLs
if (event.request?.url) {
event.request.url = event.request.url.replace(/api_key=[^&]+/g, 'api_key=REDACTED');
}

return event;
},

// Custom error grouping
beforeBreadcrumb(breadcrumb, hint) {
if (breadcrumb.category === 'console') {
return null; // Don't send console logs
}
return breadcrumb;
}
});

// Request handler (must be first middleware)
app.use(Sentry.Handlers.requestHandler());

// Tracing handler
app.use(Sentry.Handlers.tracingHandler());

console.log('✅ Sentry initialized');

return Sentry;
}

// Error handler (must be after all routes)
export function sentryErrorHandler(app) {
app.use(Sentry.Handlers.errorHandler({
shouldHandleError(error) {
// Capture all errors with status >= 500
return error.status >= 500;
}
}));
}

// Manual error capture
export function captureError(error, context = {}) {
Sentry.captureException(error, {
tags: context.tags || {},
extra: context.extra || {},
level: context.level || 'error'
});
}

// Performance monitoring
export function startTransaction(name, op) {
return Sentry.startTransaction({
name,
op,
tags: {
environment: process.env.NODE_ENV
}
});
}
