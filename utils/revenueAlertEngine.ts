// utils/revenueAlertEngine.ts
import fetch from 'node-fetch';
import ms from 'ms';

// A simple retry function to replace the one from the guide
async function retry<T>(fn: () => Promise<T>, options: { maxAttempts: number, backoff: string }): Promise<T> {
  let lastError: Error | undefined;
  for (let i = 0; i < options.maxAttempts; i++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error as Error;
      if (i < options.maxAttempts - 1) {
        const delay = options.backoff === 'exponential' ? Math.pow(2, i) * 1000 : 1000;
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }
  }
  throw lastError;
}

interface AlertChannel {
type: 'webhook' | 'email' | 'sms' | 'push' | 'discord' | 'slack';
config: Record<string, any>
enabled: boolean;
}

interface MilestoneConfig {
thresholds: number[];
channels: AlertChannel[];
templates: Record<string, any>
actions?: MilestoneAction[];
}

interface MilestoneAction {
type: 'email' | 'webhook' | 'discount' | 'feature' | 'report';
config: Record<string, any>
delay?: string; // Workflow sleep syntax
}

interface RevenueMetrics {
currentMrr: number;
previousMrr: number;
growthRate: number;
customerCount: number;
avgRevenuePerCustomer: number;
topPayingCustomers: Array<{ name: string; amount: number }>;
}

class RevenueAlertEngine {
private lastNotified: number = 0;
private alertHistory: Array<{
timestamp: Date;
threshold: number;
actualMrr: number;
channel: string;
status: 'sent' | 'failed';
}> = [];

constructor(private config: MilestoneConfig) {}

/**
* Process revenue metrics and trigger appropriate alerts
*/
async processRevenueMetrics(metrics: RevenueMetrics): Promise<void> {
"use workflow";

const nextThreshold = this.config.thresholds.find(
t => t > this.lastNotified && metrics.currentMrr >= t
);

if (!nextThreshold) return;

// Prepare enhanced alert data
const alertData = {
threshold: nextThreshold,
metrics,
previousThreshold: this.lastNotified,
growthPercentage: this.calculateGrowthPercentage(metrics),
timeToMilestone: this.calculateTimeToMilestone(metrics),
projectedNextMilestone: this.projectNextMilestone(metrics),
topContributors: metrics.topPayingCustomers.slice(0, 3),
};

// Send alerts through all enabled channels
const results = await Promise.allSettled(
this.config.channels
.filter(channel => channel.enabled)
.map(channel => this.sendAlert(channel, alertData))
);

// Log results
this.logResults(nextThreshold, metrics.currentMrr, results);

// Execute milestone actions if configured
if (this.config.actions) {
await this.executeMilestoneActions(nextThreshold, alertData);
}

// Update last notified threshold
this.lastNotified = nextThreshold;

// Store analytics
await this.storeAlertAnalytics(alertData, results);
}

private async sendAlert(channel: AlertChannel, data: any): Promise<void> {
try {
switch (channel.type) {
case 'webhook':
case 'slack':
case 'discord':
await this.sendWebhookAlert(channel, data);
break;
case 'email':
await this.sendEmailAlert(channel, data);
break;
case 'sms':
await this.sendSMSAlert(channel, data);
break;
case 'push':
await this.sendPushAlert(channel, data);
break;
default:
throw new Error(`Unknown channel type: ${channel.type}`);
}
} catch (error) {
console.error(`Failed to send ${channel.type} alert:`, error);
throw error;
}
}

private async sendWebhookAlert(channel: AlertChannel, data: any): Promise<void> {
const template = this.config.templates[channel.type] || this.config.templates.webhook;
const payload = this.formatWebhookPayload(template, data);

await retry(
() => fetch(channel.config.url, {
method: 'POST',
headers: { 'Content-Type': 'application/json', ...channel.config.headers },
body: JSON.stringify(payload),
}),
{ maxAttempts: 3, backoff: 'exponential' }
);
}

private async sendEmailAlert(channel: AlertChannel, data: any): Promise<void> {
// Implementation for email alerts (could use SendGrid, AWS SES, etc.)
const template = this.config.templates.email;
const htmlContent = this.formatEmailTemplate(template, data);

// Email sending logic here
// await emailService.send({
// to: channel.config.recipients,
// subject: `🚀 Revenue Milestone: $${data.threshold.toLocaleString()} MRR`,
// html: htmlContent
// });
}

private async sendSMSAlert(channel: AlertChannel, data: any): Promise<void> {}
private async sendPushAlert(channel: AlertChannel, data: any): Promise<void> {}


private formatWebhookPayload(template: string, data: any): any {
// Simple template replacement with more sophisticated options
return {
text: template
.replace(/\${threshold}/g, data.threshold.toLocaleString())
.replace(/\${currentMrr}/g, data.metrics.currentMrr.toLocaleString())
.replace(/\${growthRate}/g, `${data.growthPercentage.toFixed(1)}%`)
.replace(/\${customerCount}/g, data.metrics.customerCount),
attachments: [
{
title: "Revenue Metrics",
fields: [
{ title: "Current MRR", value: `$${data.metrics.currentMrr.toLocaleString()}`, short: true },
{ title: "Growth Rate", value: `${data.growthPercentage.toFixed(1)}%`, short: true },
{ title: "Customers", value: data.metrics.customerCount.toString(), short: true },
{ title: "Avg. Revenue/Customer", value: `$${data.metrics.avgRevenuePerCustomer.toFixed(2)}`, short: true },
],
color: "good"
},
{
title: "Top Contributors",
fields: data.topContributors.map((customer, i) => ({
title: `#${i+1} ${customer.name}`,
value: `$${customer.amount.toLocaleString()}`,
short: true
})),
color: "good"
},
{
title: "Projections",
fields: [
{ title: "Time to Next Milestone", value: data.timeToMilestone, short: true },
{ title: "Projected Next Milestone", value: `$${data.projectedNextMilestone.toLocaleString()}`, short: true }
],
color: "warning"
}
]
};
}

private formatEmailTemplate(template: string, data: any): string {
    return "test"
}

private calculateGrowthPercentage(metrics: RevenueMetrics): number {
return ((metrics.currentMrr - metrics.previousMrr) / metrics.previousMrr) * 100;
}

private calculateTimeToMilestone(metrics: RevenueMetrics): string {
// Calculate based on current growth rate
const nextThreshold = this.config.thresholds.find(t => t > metrics.currentMrr);
if (!nextThreshold) return "N/A";

const remaining = nextThreshold - metrics.currentMrr;
const monthlyGrowth = metrics.currentMrr * (metrics.growthRate / 100);
const monthsToMilestone = remaining / monthlyGrowth;

if (monthsToMilestone < 1) {
return `${Math.round(monthsToMilestone * 30)} days`;
}

return `${Math.round(monthsToMilestone * 10) / 10} months`;
}

private projectNextMilestone(metrics: RevenueMetrics): number {
const nextThreshold = this.config.thresholds.find(t => t > metrics.currentMrr);
return nextThreshold || 0;
}

private async executeMilestoneActions(threshold: number, data: any): Promise<void> {
if (!this.config.actions) return;

for (const action of this.config.actions) {
// Apply delay if specified
if (action.delay) {
  const delayMs = ms(action.delay);
  await new Promise(resolve => setTimeout(resolve, delayMs));
}

switch (action.type) {
case 'email':
await this.executeEmailAction(action, data);
break;
case 'webhook':
await this.executeWebhookAction(action, data);
break;
case 'discount':
await this.executeDiscountAction(action, data);
break;
case 'feature':
await this.executeFeatureAction(action, data);
break;
case 'report':
await this.executeReportAction(action, data);
break;
}
}
}

private async executeEmailAction(action: any, data: any): Promise<void> {
// Send personalized thank you emails to top customers
const topCustomers = data.topContributors.slice(0, action.config.customerCount || 5);

for (const customer of topCustomers) {
// await emailService.send({
// to: customer.email,
// template: 'milestone-thank-you',
// data: { customerName: customer.name, milestone: data.threshold }
// });
}
}

private async executeWebhookAction(action: any, data: any): Promise<void> {}
private async executeDiscountAction(action: any, data: any): Promise<void> {
// Generate discount codes for loyal customers
const discountCode = `MILESTONE${data.threshold}`;
const discountPercentage = action.config.percentage || 10;

// await discountService.create({
// code: discountCode,
// percentage: discountPercentage,
// expiresAt: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000), // 30 days
// usageLimit: action.config.usageLimit || 100
// });

// Send notification about the new discount code
await this.sendWebhookAlert({
type: 'webhook',
config: { url: process.env.DISCOUNT_WEBHOOK_URL },
enabled: true
}, {
text: `🎉 New discount code created: ${discountCode} for ${discountPercentage}% off!`,
});
}
private async executeFeatureAction(action: any, data: any): Promise<void> {}
private async executeReportAction(action: any, data: any): Promise<void> {}



private logResults(threshold: number, actualMrr: number, results: PromiseSettledResult<any>[]) {
for (const [index, result] of results.entries()) {
const channel = this.config.channels[index];
this.alertHistory.push({
timestamp: new Date(),
threshold,
actualMrr,
channel: `${channel.type}:${channel.config.url || channel.config.recipients?.join(',')}`,
status: result.status === 'fulfilled' ? 'sent' : 'failed'
});
}
}

private async storeAlertAnalytics(data: any, results: PromiseSettledResult<any>[]) {
// Store analytics for later analysis
const successCount = results.filter(r => r.status === 'fulfilled').length;

// await analyticsService.track('revenue_milestone_alert', {
// threshold: data.threshold,
// actualMrr: data.metrics.currentMrr,
// growthRate: data.growthPercentage,
// channelsSent: successCount,
// channelsTotal: results.length,
// timestamp: new Date()
// });
}

getAlertHistory() {
    return this.alertHistory;
}
}

// Singleton instance
export const revenueAlertEngine = new RevenueAlertEngine({
thresholds: [5_000, 15_000, 30_000, 50_000, 100_000, 250_000, 500_000],
channels: [
{
type: 'slack',
config: { url: process.env.SLACK_WEBHOOK_URL },
enabled: true
},
{
type: 'discord',
config: { url: process.env.DISCORD_WEBHOOK_URL },
enabled: true
},
{
type: 'email',
config: { recipients: ['team@company.com', 'executives@company.com'] },
enabled: true
}
],
templates: {
webhook: `🚀 *Milestone reached!* Current CI-metered MRR: **$${'${currentMrr}'}** (≥ $${'${threshold}'})`,
email: `

🎉 Revenue Milestone Achieved!


Congratulations team! We've just reached $${'${threshold}'} in MRR!




Current MRR: $${'${currentMrr}'}


Growth Rate: ${'${growthRate}'}%


Total Customers: ${'${customerCount}'}




Keep up the great work!

`,
discord: `🚀 **Milestone reached!** Current CI-metered MRR: **$${'${currentMrr}'}** (≥ $${'${threshold}'})`
},
actions: [
{
type: 'email',
config: { customerCount: 5 },
delay: '1 hour'
},
{
type: 'discount',
config: { percentage: 15, usageLimit: 50 },
delay: '2 hours'
},
{
type: 'report',
config: { includeProjections: true },
delay: '1 day'
}
]
});

export async function processRevenueMilestone(metrics: RevenueMetrics): Promise<void> {
return revenueAlertEngine.processRevenueMetrics(metrics);
}
