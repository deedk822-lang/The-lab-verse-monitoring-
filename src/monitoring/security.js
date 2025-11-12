import helmet from 'helmet';
import rateLimit from 'express-rate-limit';
import { metrics } from '@opentelemetry/api';

const meter = metrics.getMeter('security', '1.0.0');

// Security metrics
const securityEvents = meter.createCounter('security_events_total', {
description: 'Security events detected',
unit: '1'
});

const rateLimitHits = meter.createCounter('rate_limit_hits_total', {
description: 'Rate limit violations',
unit: '1'
});

/**
* Configure security headers
*/
export function configureSecurityHeaders(app) {
app.use(helmet({
contentSecurityPolicy: {
directives: {
defaultSrc: ["'self'"],
scriptSrc: ["'self'", "'unsafe-inline'", "https://vercel.live"],
styleSrc: ["'self'", "'unsafe-inline'"],
imgSrc: ["'self'", "data:", "https:"],
connectSrc: ["'self'", "https://vercel.live", "https://*.grafana.net"],
fontSrc: ["'self'", "data:"],
objectSrc: ["'none'"],
mediaSrc: ["'self'"],
frameSrc: ["'none'"]
}
},
hsts: {
maxAge: 31536000,
includeSubDomains: true,
preload: true
},
referrerPolicy: {
policy: 'strict-origin-when-cross-origin'
}
}));

console.log('✅ Security headers configured');
}

/**
* Configure rate limiting
*/
export function configureRateLimiting(app) {
// General API rate limit
const apiLimiter = rateLimit({
windowMs: 15 * 60 * 1000, // 15 minutes
max: 100, // 100 requests per window
message: 'Too many requests from this IP, please try again later',
standardHeaders: true,
legacyHeaders: false,
handler: (req, res) => {
rateLimitHits.add(1, {
ip: req.ip,
path: req.path
});

res.status(429).json({
error: 'Too many requests',
retryAfter: req.rateLimit.resetTime
});
}
});

// Stricter limit for AI endpoints
const aiLimiter = rateLimit({
windowMs: 60 * 1000, // 1 minute
max: 10, // 10 requests per minute
message: 'AI request rate limit exceeded',
skipSuccessfulRequests: false
});

app.use('/api/', apiLimiter);
app.use('/api/research', aiLimiter);
app.use('/api/generate', aiLimiter);

console.log('✅ Rate limiting configured');
}

/**
* Track suspicious activity
*/
export function trackSuspiciousActivity(type, details) {
securityEvents.add(1, {
event_type: type,
severity: details.severity || 'medium'
});

console.warn(`🚨 Security Event: ${type}`, details);
}

/**
* Middleware to detect suspicious requests
*/
export function suspiciousActivityDetector(req, res, next) {
const suspiciousPatterns = [
/(\.\.|\/etc\/|\/proc\/)/i, // Path traversal
/(union|select|insert|update|delete|drop|exec|script)/i, // SQL injection
/(<|>|'|"|`|;|\||&|%|#|\(|\)|\[|\]|\{|\}|\$)/, // XSS and other injection
/(\.\.\/|\.\.\\)/, // Directory traversal
/(\${|<%|%{)/ // Template injection
];

const requestString = `${req.url} ${JSON.stringify(req.body)} ${JSON.stringify(req.query)}`;

for (const pattern of suspiciousPatterns) {
if (pattern.test(requestString)) {
trackSuspiciousActivity('suspicious_pattern_detected', {
ip: req.ip,
path: req.path,
pattern: pattern.toString(),
severity: 'high'
});

return res.status(400).json({
error: 'Invalid request detected'
});
}
}

next();
}

/**
* API key validation middleware
*/
export function validateApiKey(req, res, next) {
const apiKey = req.headers['x-api-key'];

if (!apiKey) {
trackSuspiciousActivity('missing_api_key', {
ip: req.ip,
path: req.path,
severity: 'low'
});

return res.status(401).json({
error: 'API key required'
});
}

// Validate API key (implement your validation logic)
const validKeys = process.env.VALID_API_KEYS?.split(',') || [];

if (!validKeys.includes(apiKey)) {
trackSuspiciousActivity('invalid_api_key', {
ip: req.ip,
path: req.path,
severity: 'high'
});

return res.status(403).json({
error: 'Invalid API key'
});
}

next();
}

/**
* CORS configuration
*/
export function configureCORS(app) {
const cors = require('cors');

const allowedOrigins = process.env.ALLOWED_ORIGINS?.split(',') || [
'https://the-lab-verse-monitoring.vercel.app',
'http://localhost:3000'
];

app.use(cors({
origin: (origin, callback) => {
if (!origin || allowedOrigins.includes(origin)) {
callback(null, true);
} else {
trackSuspiciousActivity('cors_violation', {
origin,
severity: 'medium'
});
callback(new Error('Not allowed by CORS'));
}
},
credentials: true,
methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
allowedHeaders: ['Content-Type', 'Authorization', 'X-API-Key']
}));

console.log('✅ CORS configured');
}
