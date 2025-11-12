import { trace, metrics, context } from '@opentelemetry/api';

const tracer = trace.getTracer('rum', '1.0.0');
const meter = metrics.getMeter('rum', '1.0.0');

// RUM Metrics
const pageLoadTime = meter.createHistogram('rum_page_load_time', {
description: 'Page load time from RUM',
unit: 'ms'
});

const userInteractions = meter.createCounter('rum_user_interactions', {
description: 'User interaction events',
unit: '1'
});

const errorRate = meter.createCounter('rum_errors_total', {
description: 'Client-side errors',
unit: '1'
});

// Track page views
export function trackPageView(path, metadata = {}) {
const span = tracer.startSpan('page.view', {
attributes: {
'page.path': path,
'page.referrer': document.referrer,
'user.agent': navigator.userAgent,
...metadata
}
});

span.end();
}

// Track user interactions
export function trackInteraction(type, target, metadata = {}) {
userInteractions.add(1, {
interaction_type: type,
target: target,
...metadata
});
}

// Track errors
export function trackError(error, metadata = {}) {
errorRate.add(1, {
error_type: error.name,
error_message: error.message,
...metadata
});

const span = tracer.startSpan('error.client', {
attributes: {
'error.type': error.name,
'error.message': error.message,
'error.stack': error.stack,
...metadata
}
});

span.setStatus({ code: 2, message: error.message });
span.recordException(error);
span.end();
}

// Track Web Vitals
export function trackWebVitals() {
if (typeof window === 'undefined') return;

// FCP - First Contentful Paint
new PerformanceObserver((list) => {
for (const entry of list.getEntries()) {
if (entry.name === 'first-contentful-paint') {
pageLoadTime.record(entry.startTime, {
metric: 'fcp'
});
}
}
}).observe({ entryTypes: ['paint'] });

// LCP - Largest Contentful Paint
new PerformanceObserver((list) => {
const entries = list.getEntries();
const lastEntry = entries[entries.length - 1];
pageLoadTime.record(lastEntry.renderTime || lastEntry.loadTime, {
metric: 'lcp'
});
}).observe({ entryTypes: ['largest-contentful-paint'] });

// FID - First Input Delay
new PerformanceObserver((list) => {
for (const entry of list.getEntries()) {
pageLoadTime.record(entry.processingStart - entry.startTime, {
metric: 'fid'
});
}
}).observe({ entryTypes: ['first-input'] });

// CLS - Cumulative Layout Shift
let clsValue = 0;
new PerformanceObserver((list) => {
for (const entry of list.getEntries()) {
if (!entry.hadRecentInput) {
clsValue += entry.value;
pageLoadTime.record(clsValue * 1000, {
metric: 'cls'
});
}
}
}).observe({ entryTypes: ['layout-shift'] });
}

// Initialize RUM
export function initializeRUM() {
if (typeof window === 'undefined') return;

console.log('✅ RUM initialized');

// Track page load
window.addEventListener('load', () => {
const loadTime = performance.timing.loadEventEnd - performance.timing.navigationStart;
pageLoadTime.record(loadTime, { metric: 'page_load' });
});

// Track Web Vitals
trackWebVitals();

// Track errors
window.addEventListener('error', (event) => {
trackError(event.error || new Error(event.message));
});

window.addEventListener('unhandledrejection', (event) => {
trackError(new Error(event.reason));
});

// Track user interactions
['click', 'submit', 'change'].forEach(eventType => {
document.addEventListener(eventType, (event) => {
trackInteraction(eventType, event.target.tagName);
});
});
}
