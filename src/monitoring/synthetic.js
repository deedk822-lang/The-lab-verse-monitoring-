import axios from 'axios';
import { metrics } from '@opentelemetry/api';

const meter = metrics.getMeter('synthetic-monitoring', '1.0.0');

// Synthetic monitoring metrics
const uptimeCheck = meter.createCounter('synthetic_uptime_checks_total', {
description: 'Synthetic uptime check results',
unit: '1'
});

const responseTime = meter.createHistogram('synthetic_response_time_seconds', {
description: 'Synthetic check response time',
unit: 's'
});

export class SyntheticMonitor {
constructor(config = {}) {
this.endpoints = config.endpoints || [
{ name: 'health', url: 'http://localhost:3001/health', method: 'GET' },
{ name: 'api', url: 'http://localhost:3001/api/research', method: 'POST', body: { q: 'test' } }
];
this.interval = config.interval || 60000; // 1 minute
this.timeout = config.timeout || 10000; // 10 seconds
this.running = false;
this.results = new Map();
}

/**
* Start synthetic monitoring
*/
start() {
if (this.running) {
console.warn('Synthetic monitoring already running');
return;
}

this.running = true;
console.log('✅ Synthetic monitoring started');

// Run checks immediately
this.runChecks();

// Schedule periodic checks
this.intervalId = setInterval(() => {
this.runChecks();
}, this.interval);
}

/**
* Stop synthetic monitoring
*/
stop() {
if (this.intervalId) {
clearInterval(this.intervalId);
this.running = false;
console.log('⏹️ Synthetic monitoring stopped');
}
}

/**
* Run all checks
*/
async runChecks() {
const promises = this.endpoints.map(endpoint => this.checkEndpoint(endpoint));
await Promise.allSettled(promises);
}

/**
* Check a single endpoint
*/
async checkEndpoint(endpoint) {
const startTime = Date.now();

try {
const response = await axios({
method: endpoint.method,
url: endpoint.url,
data: endpoint.body,
timeout: this.timeout,
validateStatus: () => true // Don't throw on any status
});

const duration = (Date.now() - startTime) / 1000;
const success = response.status >= 200 && response.status < 300;

// Record metrics
uptimeCheck.add(1, {
endpoint: endpoint.name,
status: success ? 'up' : 'down',
http_status: response.status
});

responseTime.record(duration, {
endpoint: endpoint.name
});

// Store result
this.results.set(endpoint.name, {
timestamp: new Date().toISOString(),
success,
status: response.status,
duration,
error: null
});

if (!success) {
console.error(`❌ Synthetic check failed for ${endpoint.name}: HTTP ${response.status}`);
}

return { success, duration, status: response.status };

} catch (error) {
const duration = (Date.now() - startTime) / 1000;

// Record failure
uptimeCheck.add(1, {
endpoint: endpoint.name,
status: 'down',
error_type: error.code || 'unknown'
});

// Store result
this.results.set(endpoint.name, {
timestamp: new Date().toISOString(),
success: false,
status: 0,
duration,
error: error.message
});

console.error(`❌ Synthetic check error for ${endpoint.name}:`, error.message);

return { success: false, duration, error: error.message };
}
}

/**
* Get current status
*/
getStatus() {
const status = {};

for (const [name, result] of this.results.entries()) {
status[name] = {
...result,
age: Date.now() - new Date(result.timestamp).getTime()
};
}

return status;
}

/**
* Get uptime percentage
*/
getUptimePercentage(endpointName, period = 3600000) { // Default 1 hour
// This would need to store historical data
// For now, return current status
const result = this.results.get(endpointName);
return result?.success ? 100 : 0;
}
}

// Export singleton instance
export const syntheticMonitor = new SyntheticMonitor();

// Auto-start if not in test environment
if (process.env.NODE_ENV !== 'test') {
syntheticMonitor.start();
}
