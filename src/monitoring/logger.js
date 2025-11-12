import winston from 'winston';
import { format } from 'winston';

const { combine, timestamp, json, colorize, printf, errors } = format;

// Custom format for console output
const consoleFormat = printf(({ level, message, timestamp, ...metadata }) => {
let msg = `${timestamp} [${level}] : ${message}`;

if (Object.keys(metadata).length > 0) {
msg += ` ${JSON.stringify(metadata)}`;
}

return msg;
});

// Create logger instance
export const logger = winston.createLogger({
level: process.env.LOG_LEVEL || 'info',
format: combine(
errors({ stack: true }),
timestamp({ format: 'YYYY-MM-DD HH:mm:ss' }),
json()
),
defaultMeta: {
service: 'ai-provider-monitoring',
environment: process.env.NODE_ENV,
version: process.env.npm_package_version
},
transports: [
// Console transport
new winston.transports.Console({
format: combine(
colorize(),
consoleFormat
)
}),

// File transport for errors
new winston.transports.File({
filename: 'logs/error.log',
level: 'error',
maxsize: 5242880, // 5MB
maxFiles: 5
}),

// File transport for all logs
new winston.transports.File({
filename: 'logs/combined.log',
maxsize: 5242880,
maxFiles: 5
})
]
});

// Add Grafana Loki transport if configured
if (process.env.LOKI_URL) {
const LokiTransport = require('winston-loki');

logger.add(new LokiTransport({
host: process.env.LOKI_URL,
labels: {
app: 'ai-provider-monitoring',
environment: process.env.NODE_ENV
},
json: true,
format: json(),
replaceTimestamp: true,
onConnectionError: (err) => console.error('Loki connection error:', err)
}));
}

// Helper functions
export const log = {
info: (message, meta = {}) => logger.info(message, meta),
error: (message, error, meta = {}) => logger.error(message, { error: error.message, stack: error.stack, ...meta }),
warn: (message, meta = {}) => logger.warn(message, meta),
debug: (message, meta = {}) => logger.debug(message, meta),

// AI-specific logging
aiRequest: (provider, model, duration, tokens, meta = {}) => {
logger.info('AI Request', {
type: 'ai_request',
provider,
model,
duration,
tokens,
...meta
});
},

aiError: (provider, error, meta = {}) => {
logger.error('AI Error', {
type: 'ai_error',
provider,
error: error.message,
stack: error.stack,
...meta
});
}
};

// Express middleware for request logging
export function requestLogger(req, res, next) {
const start = Date.now();

res.on('finish', () => {
const duration = Date.now() - start;

logger.info('HTTP Request', {
type: 'http_request',
method: req.method,
url: req.url,
status: res.statusCode,
duration,
ip: req.ip,
userAgent: req.get('user-agent')
});
});

next();
}
