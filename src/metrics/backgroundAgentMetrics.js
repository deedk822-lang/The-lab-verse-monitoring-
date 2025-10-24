import { register, Counter, Histogram, Gauge, Summary } from 'prom-client';

// Background Agent Zapier Integration Metrics

const backgroundAgentRequests = new Counter({
  name: 'background_agent_zapier_requests_total',
  help: 'Total number of background agent requests to Zapier',
  labelNames: ['agent_id', 'action', 'status', 'priority']
});

const backgroundAgentResponseTime = new Histogram({
  name: 'background_agent_zapier_response_time_seconds',
  help: 'Response time for background agent Zapier requests',
  labelNames: ['agent_id', 'action'],
  buckets: [0.1, 0.5, 1, 2, 5, 10, 30, 60]
});

const backgroundAgentErrors = new Counter({
  name: 'background_agent_zapier_errors_total',
  help: 'Total number of background agent Zapier errors',
  labelNames: ['agent_id', 'error_type', 'action']
});

const activeBackgroundAgents = new Gauge({
  name: 'background_agents_active',
  help: 'Number of active background agents',
  labelNames: ['agent_type', 'status']
});

const backgroundAgentQueueSize = new Gauge({
  name: 'background_agent_queue_size',
  help: 'Number of tasks in background agent queue',
  labelNames: ['agent_id', 'priority']
});

const backgroundAgentProcessingTime = new Summary({
  name: 'background_agent_processing_time_seconds',
  help: 'Time spent processing tasks by background agents',
  labelNames: ['agent_id', 'task_type'],
  percentiles: [0.5, 0.9, 0.95, 0.99]
});

const zapierWebhookSuccessRate = new Gauge({
  name: 'zapier_webhook_success_rate',
  help: 'Success rate of Zapier webhook calls',
  labelNames: ['agent_id', 'action']
});

const backgroundAgentMemoryUsage = new Gauge({
  name: 'background_agent_memory_usage_bytes',
  help: 'Memory usage of background agents',
  labelNames: ['agent_id']
});

const backgroundAgentCpuUsage = new Gauge({
  name: 'background_agent_cpu_usage_percent',
  help: 'CPU usage of background agents',
  labelNames: ['agent_id']
});

// Background Agent Health Metrics
const backgroundAgentHealth = new Gauge({
  name: 'background_agent_health_status',
  help: 'Health status of background agents (1 = healthy, 0 = unhealthy)',
  labelNames: ['agent_id', 'component']
});

const backgroundAgentLastActivity = new Gauge({
  name: 'background_agent_last_activity_timestamp',
  help: 'Timestamp of last activity for background agents',
  labelNames: ['agent_id']
});

// Zapier Integration Specific Metrics
const zapierWebhookLatency = new Histogram({
  name: 'zapier_webhook_latency_seconds',
  help: 'Latency of Zapier webhook calls',
  labelNames: ['webhook_type', 'status'],
  buckets: [0.1, 0.5, 1, 2, 5, 10, 30, 60]
});

const zapierWebhookRetries = new Counter({
  name: 'zapier_webhook_retries_total',
  help: 'Total number of Zapier webhook retries',
  labelNames: ['agent_id', 'action', 'retry_attempt']
});

const zapierWebhookTimeouts = new Counter({
  name: 'zapier_webhook_timeouts_total',
  help: 'Total number of Zapier webhook timeouts',
  labelNames: ['agent_id', 'action']
});

// Background Agent Task Metrics
const backgroundAgentTasksProcessed = new Counter({
  name: 'background_agent_tasks_processed_total',
  help: 'Total number of tasks processed by background agents',
  labelNames: ['agent_id', 'task_type', 'status']
});

const backgroundAgentTaskDuration = new Histogram({
  name: 'background_agent_task_duration_seconds',
  help: 'Duration of background agent task processing',
  labelNames: ['agent_id', 'task_type'],
  buckets: [0.1, 0.5, 1, 2, 5, 10, 30, 60, 120, 300]
});

// Background Agent Resource Metrics
const backgroundAgentConnections = new Gauge({
  name: 'background_agent_connections_active',
  help: 'Number of active connections for background agents',
  labelNames: ['agent_id', 'connection_type']
});

const backgroundAgentThroughput = new Gauge({
  name: 'background_agent_throughput_per_second',
  help: 'Throughput of background agents (tasks per second)',
  labelNames: ['agent_id']
});

// Background Agent Error Metrics
const backgroundAgentErrorRate = new Gauge({
  name: 'background_agent_error_rate',
  help: 'Error rate of background agents (errors per second)',
  labelNames: ['agent_id']
});

const backgroundAgentConsecutiveErrors = new Gauge({
  name: 'background_agent_consecutive_errors',
  help: 'Number of consecutive errors for background agents',
  labelNames: ['agent_id']
});

// Background Agent Performance Metrics
const backgroundAgentEfficiency = new Gauge({
  name: 'background_agent_efficiency_ratio',
  help: 'Efficiency ratio of background agents (successful tasks / total tasks)',
  labelNames: ['agent_id']
});

const backgroundAgentUtilization = new Gauge({
  name: 'background_agent_utilization_percent',
  help: 'Utilization percentage of background agents',
  labelNames: ['agent_id']
});

// Background Agent Configuration Metrics
const backgroundAgentConfigVersion = new Gauge({
  name: 'background_agent_config_version',
  help: 'Configuration version of background agents',
  labelNames: ['agent_id']
});

const backgroundAgentFeatureFlags = new Gauge({
  name: 'background_agent_feature_flags',
  help: 'Feature flags enabled for background agents',
  labelNames: ['agent_id', 'feature']
});

// Export all metrics
export {
  backgroundAgentRequests,
  backgroundAgentResponseTime,
  backgroundAgentErrors,
  activeBackgroundAgents,
  backgroundAgentQueueSize,
  backgroundAgentProcessingTime,
  zapierWebhookSuccessRate,
  backgroundAgentMemoryUsage,
  backgroundAgentCpuUsage,
  backgroundAgentHealth,
  backgroundAgentLastActivity,
  zapierWebhookLatency,
  zapierWebhookRetries,
  zapierWebhookTimeouts,
  backgroundAgentTasksProcessed,
  backgroundAgentTaskDuration,
  backgroundAgentConnections,
  backgroundAgentThroughput,
  backgroundAgentErrorRate,
  backgroundAgentConsecutiveErrors,
  backgroundAgentEfficiency,
  backgroundAgentUtilization,
  backgroundAgentConfigVersion,
  backgroundAgentFeatureFlags
};

// Helper functions for updating metrics
export const updateBackgroundAgentRequest = (agentId, action, status, priority = 'normal') => {
  backgroundAgentRequests.inc({ agent_id: agentId, action, status, priority });
};

export const updateBackgroundAgentResponseTime = (agentId, action, duration) => {
  backgroundAgentResponseTime.observe({ agent_id: agentId, action }, duration);
};

export const updateBackgroundAgentError = (agentId, errorType, action) => {
  backgroundAgentErrors.inc({ agent_id: agentId, error_type: errorType, action });
};

export const updateActiveBackgroundAgents = (agentType, status, count) => {
  activeBackgroundAgents.set({ agent_type: agentType, status }, count);
};

export const updateBackgroundAgentQueueSize = (agentId, priority, size) => {
  backgroundAgentQueueSize.set({ agent_id: agentId, priority }, size);
};

export const updateBackgroundAgentProcessingTime = (agentId, taskType, duration) => {
  backgroundAgentProcessingTime.observe({ agent_id: agentId, task_type: taskType }, duration);
};

export const updateZapierWebhookSuccessRate = (agentId, action, successRate) => {
  zapierWebhookSuccessRate.set({ agent_id: agentId, action }, successRate);
};

export const updateBackgroundAgentHealth = (agentId, component, isHealthy) => {
  backgroundAgentHealth.set({ agent_id: agentId, component }, isHealthy ? 1 : 0);
};

export const updateBackgroundAgentLastActivity = (agentId) => {
  backgroundAgentLastActivity.set({ agent_id: agentId }, Date.now() / 1000);
};

export const updateZapierWebhookLatency = (webhookType, status, latency) => {
  zapierWebhookLatency.observe({ webhook_type: webhookType, status }, latency);
};

export const updateZapierWebhookRetries = (agentId, action, retryAttempt) => {
  zapierWebhookRetries.inc({ agent_id: agentId, action, retry_attempt: retryAttempt });
};

export const updateZapierWebhookTimeouts = (agentId, action) => {
  zapierWebhookTimeouts.inc({ agent_id: agentId, action });
};

export const updateBackgroundAgentTasksProcessed = (agentId, taskType, status) => {
  backgroundAgentTasksProcessed.inc({ agent_id: agentId, task_type: taskType, status });
};

export const updateBackgroundAgentTaskDuration = (agentId, taskType, duration) => {
  backgroundAgentTaskDuration.observe({ agent_id: agentId, task_type: taskType }, duration);
};

export const updateBackgroundAgentConnections = (agentId, connectionType, count) => {
  backgroundAgentConnections.set({ agent_id: agentId, connection_type: connectionType }, count);
};

export const updateBackgroundAgentThroughput = (agentId, throughput) => {
  backgroundAgentThroughput.set({ agent_id: agentId }, throughput);
};

export const updateBackgroundAgentErrorRate = (agentId, errorRate) => {
  backgroundAgentErrorRate.set({ agent_id: agentId }, errorRate);
};

export const updateBackgroundAgentConsecutiveErrors = (agentId, consecutiveErrors) => {
  backgroundAgentConsecutiveErrors.set({ agent_id: agentId }, consecutiveErrors);
};

export const updateBackgroundAgentEfficiency = (agentId, efficiency) => {
  backgroundAgentEfficiency.set({ agent_id: agentId }, efficiency);
};

export const updateBackgroundAgentUtilization = (agentId, utilization) => {
  backgroundAgentUtilization.set({ agent_id: agentId }, utilization);
};

export const updateBackgroundAgentConfigVersion = (agentId, version) => {
  backgroundAgentConfigVersion.set({ agent_id: agentId }, version);
};

export const updateBackgroundAgentFeatureFlags = (agentId, feature, enabled) => {
  backgroundAgentFeatureFlags.set({ agent_id: agentId, feature }, enabled ? 1 : 0);
};