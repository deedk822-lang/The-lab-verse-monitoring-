// ultimateAiDealHunter.ts
import { chromium, Browser, Page } from 'playwright';
import fetch from 'node-fetch';
import { formatISO, addDays, isAfter, isBefore } from 'date-fns';
import { Redis } from 'ioredis';
import { JSDOM } from 'jsdom';
import { OpenAI } from 'openai';
import * as fs from 'fs/promises';
import * as path from 'path';
import { Worker } from 'worker_threads';
import { createPool } from 'generic-pool';

// ---------- CONFIG ----------
const SOURCES = [
// Official AI-tool pages
{
name: 'OpenAI',
url: 'https://openai.com/pricing',
category: 'llm',
reliability: 0.95,
extractionMethod: 'ai'
},
{
name: 'Anthropic',
url: 'https://www.anthropic.com/pricing',
category: 'llm',
reliability: 0.95,
extractionMethod: 'ai'
},
{
name: 'Cohere',
url: 'https://cohere.com/pricing',
category: 'llm',
reliability: 0.90,
extractionMethod: 'hybrid'
},
{
name: 'Stability AI',
url: 'https://platform.stability.ai/docs/getting-started',
category: 'image',
reliability: 0.85,
extractionMethod: 'hybrid'
},
{
name: 'Replicate',
url: 'https://replicate.com/pricing',
category: 'platform',
reliability: 0.90,
extractionMethod: 'ai'
},
{
name: 'Hugging Face',
url: 'https://huggingface.co/pricing',
category: 'platform',
reliability: 0.95,
extractionMethod: 'ai'
},

// Aggregators & community sources
{
name: 'Product Hunt AI',
url: 'https://www.producthunt.com/topics/artificial-intelligence',
category: 'aggregator',
reliability: 0.75,
extractionMethod: 'dom'
},
{
name: 'Reddit r/AI',
url: 'https://www.reddit.com/r/ArtificialIntelligence/search?q=free+trial&restrict_sr=1',
category: 'community',
reliability: 0.70,
extractionMethod: 'dom'
},
{
name: 'Hacker News',
url: 'https://hn.algolia.com/api/v1/search?query=free%20trial%20AI',
category: 'community',
reliability: 0.65,
extractionMethod: 'api'
},
{
name: 'AI-Tools GitHub',
url: 'https://raw.githubusercontent.com/ai-collection/awesome-ai-tools/main/README.md',
category: 'curation',
reliability: 0.80,
extractionMethod: 'markdown'
},
{
name: 'SaaSHub',
url: 'https://www.saashub.com/search?q=ai%20tools',
category: 'aggregator',
reliability: 0.80,
extractionMethod: 'dom'
},
{
name: 'AlternativeTo',
url: 'https://alternativeto.net/browse/search/?q=ai%20tools',
category: 'aggregator',
reliability: 0.75,
extractionMethod: 'dom'
},
{
name: 'Indie Hackers',
url: 'https://www.indiehackers.com/products?search=ai',
category: 'community',
reliability: 0.70,
extractionMethod: 'dom'
},
{
name: 'AngelList',
url: 'https://angel.co/company/jobs?q=ai',
category: 'community',
reliability: 0.65,
extractionMethod: 'dom'
}
];

const CONFIG = {
MAX_RESULTS: 15,
CACHE_TTL_HOURS: 24,
PARALLEL_SCRAPES: 5,
PROXY_ROTATION: true,
AI_EXTRACTION: true,
NOTIFICATION_CHANNELS: {
slack: process.env.SLACK_WEBHOOK_URL,
discord: process.env.DISCORD_WEBHOOK_URL,
email: process.env.EMAIL_SERVICE_URL,
sms: process.env.SMS_SERVICE_URL,
webhook: process.env.GENERIC_WEBHOOK_URL
},
REDIS_URL: process.env.REDIS_URL || 'redis://localhost:6379',
OPENAI_API_KEY: process.env.OPENAI_API_KEY,
CACHE_FILE: path.resolve('.dealCache.json'),
WORKER_POOL_SIZE: 3
};

// Initialize Redis for persistence
const redis = new Redis(CONFIG.REDIS_URL);

// Initialize OpenAI for content analysis
const openai = new OpenAI({ apiKey: CONFIG.OPENAI_API_KEY });

// Create browser pool for parallel scraping
const browserPool = createPool({
create: async () => {
const browser = await chromium.launch({
headless: true,
args: [
'--disable-blink-features=AutomationControlled',
'--disable-web-security',
'--disable-features=VizDisplayCompositor'
]
});
return browser;
},
destroy: async (browser) => {
await browser.close();
},
max: CONFIG.WORKER_POOL_SIZE,
min: 1,
acquireTimeoutMillis: 30000,
createTimeoutMillis: 30000,
destroyTimeoutMillis: 5000,
idleTimeoutMillis: 30000,
reapIntervalMillis: 1000,
createRetryIntervalMillis: 200
});

// Worker for parallel scraping
function createScrapeWorker() {
return new Worker(`
const { chromium } = require('playwright');
const { JSDOM } = require('jsdom');
const { parentPort, workerData } = require('worker_threads');

async function scrapeSource(source) {
let browser = null;
let page = null;

try {
browser = await chromium.launch({
headless: true,
args: [
'--disable-blink-features=AutomationControlled',
'--disable-web-security',
'--disable-features=VizDisplayCompositor'
]
});

page = await browser.newPage();
await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36');

// Add random delay to avoid detection
await page.waitForTimeout(Math.random() * 2000 + 1000);

await page.goto(source.url, {
waitUntil: 'domcontentloaded',
timeout: 30000
});

const content = await page.content();

// Different extraction methods based on source
let offers = [];

if (source.extractionMethod === 'ai') {
// For high-reliability sources, use AI extraction
offers = await extractWithAI(content, source);
} else if (source.extractionMethod === 'api') {
// For API-based sources, parse JSON directly
offers = await extractFromAPI(content, source);
} else if (source.extractionMethod === 'markdown') {
// For markdown sources, parse with markdown parser
offers = await extractFromMarkdown(content, source);
} else {
// Default to DOM extraction
offers = await extractWithDOM(content, source);
}

parentPort.postMessage({
success: true,
source: source.name,
offers
});
} catch (error) {
parentPort.postMessage({
success: false,
source: source.name,
error: error.message
});
} finally {
if (page) await page.close();
if (browser) await browser.close();
}
}

// Listen for messages from main thread
parentPort.on('message', (source) => {
scrapeSource(source);
});
`, { eval: true });
}

// Create worker pool
const workerPool = [];
for (let i = 0; i < CONFIG.WORKER_POOL_SIZE; i++) {
workerPool.push(createScrapeWorker());
}

type Offer = {
id: string;
provider: string;
category: string;
title: string;
description: string;
trialDays?: number;
creditUSD?: number;
originalPrice?: number;
discountPercentage?: number;
expiry?: string; // ISO date
coupon?: string;
url: string;
source: string;
reliability: number;
popularity?: number;
score: number;
scrapedAt: string;
features?: string[];
limitations?: string[];
targetAudience?: string[];
extractionMethod: string;
};

type DealHistory = {
dealId: string;
firstSeen: string;
lastSeen: string;
priceHistory: Array<{
price: number;
date: string;
}>;
occurrenceCount: number;
averageScore: number;
trending: boolean;
};

// Advanced scoring with multiple factors
function computeScore(o: Offer): number {
// Base value factors
const creditScore = (o.creditUSD ?? 0) * 0.25;
const durationScore = (o.trialDays ?? 0) * 0.15;
const discountScore = (o.discountPercentage ?? 0) * (o.originalPrice ?? 0) * 0.2;

// Urgency factors
let urgencyScore = 0;
if (o.expiry) {
const daysUntilExpiry = (new Date(o.expiry).getTime() - Date.now()) / (1000 * 60 * 60 * 24);
if (daysUntilExpiry < 3) urgencyScore = 20; // High urgency for expiring soon
else if (daysUntilExpiry < 7) urgencyScore = 10; // Medium urgency
else if (daysUntilExpiry < 30) urgencyScore = 5; // Low urgency
}

// Quality factors
const reliabilityScore = o.reliability * 10;
const featureScore = (o.features?.length ?? 0) * 2;

// Popularity factor (how often we've seen this deal)
const popularityScore = Math.min((o.popularity ?? 0) * 0.1, 5);

// Trending factor (if deal is getting more popular)
const trendingScore = o.trending ? 10 : 0;

return creditScore + durationScore + discountScore + urgencyScore + reliabilityScore + featureScore + popularityScore + trendingScore;
}

// AI-assisted content extraction
async function extractWithAI(content: string, source: { name: string; category: string }): Promise<any[]> {
const prompt = `
Extract AI tool deals from the following content from ${source.name} (${source.category}).

Look for:
- Free trials (duration in days)
- Free credits (amount in USD)
- Discounts (percentage or amount)
- Coupon codes
- Expiry dates
- Feature lists
- Limitations
- Target audience
- Original pricing
- Popularity indicators (upvotes, stars, etc.)

Return a JSON array of deals with this structure:
[
{
"title": "Deal title",
"description": "Brief description",
"trialDays": 30,
"creditUSD": 50,
"originalPrice": 100,
"discountPercentage": 50,
"expiry": "2023-12-31",
"coupon": "SAVE50",
"url": "https://example.com/deal",
"features": ["Feature 1", "Feature 2"],
"limitations": ["Limitation 1"],
"targetAudience": ["Developers", "Enterprises"],
"popularity": 100
}
]

Content:
${content.substring(0, 8000)} // Limit content to avoid token limits
`;

const response = await openai.chat.completions.create({
model: "gpt-4",
messages: [{ role: "user", content: prompt }],
temperature: 0.2,
response_format: { type: "json_object" }
});

const data = JSON.parse(response.choices[0].message.content || '{}');
return data.offers || [];
}

// API-based extraction for structured sources
async function extractFromAPI(content: string, source: { name: string; category: string }): Promise<any[]> {
try {
const data = JSON.parse(content);
const offers: Offer[] = [];

// Handle different API response formats
if (Array.isArray(data.hits)) {
// Hacker News format
for (const hit of data.hits) {
if (hit.title && hit.url && hit.story_text) {
const { days, usd } = parseNumbers(hit.story_text);
const coupon = extractCouponCode(hit.story_text);

if (days || usd || coupon) {
offers.push({
provider: source.name,
category: source.category,
title: hit.title,
description: hit.story_text.substring(0, 200),
trialDays: days,
creditUSD: usd,
coupon,
url: hit.url,
popularity: hit.points || 0,
extractionMethod: 'api',
scrapedAt: new Date().toISOString()
} as Offer);
}
}
}
}

return offers;
} catch (error) {
console.error(`API extraction failed for ${source.name}:`, error);
return [];
}
}

// Markdown extraction for GitHub README files
async function extractFromMarkdown(content: string, source: { name: string; category: string }): Promise<any[]> {
const offers: Offer[] = [];

// Split content by sections
const sections = content.split(/##\s+/g);

for (const section of sections) {
// Look for tool entries with deal indicators
if (/(free trial|free credits?|promo|discount|coupon|credit)/i.test(section)) {
const lines = section.split('\n');
let title = '';
let description = '';

for (const line of lines) {
// Extract title (usually a link)
const titleMatch = line.match(/\[([^\]]+)\]\(([^)]+)\)/);
if (titleMatch && !title) {
title = titleMatch[1];
continue;
}

// Extract description
if (line.trim() && !line.startsWith('#') && !line.startsWith('[')) {
description += line + ' ';
}
}

// Extract deal details
const { days, usd } = parseNumbers(section);
const coupon = extractCouponCode(section);

if (title && (days || usd || coupon)) {
offers.push({
provider: source.name,
category: source.category,
title,
description: description.trim().substring(0, 200),
trialDays: days,
creditUSD: usd,
coupon,
url: '', // Would need to extract from the title link
extractionMethod: 'markdown',
scrapedAt: new Date().toISOString()
} as Offer);
}
}
}

return offers;
}

// DOM-based extraction for web pages
async function extractWithDOM(content: string, source: { name: string; category: string; reliability: number }): Promise<any[]> {
const dom = new JSDOM(content);
const document = dom.window.document;

const offers: Offer[] = [];

// Look for pricing sections, promo banners, etc.
const pricingSections = document.querySelectorAll('.pricing, .plans, .promo, .deal, .offer');

for (const section of pricingSections) {
const textContent = section.textContent || '';

// Skip if no deal indicators
if (!/(free trial|free credits?|promo|discount|coupon|credit|save)/i.test(textContent)) continue;

// Extract basic information
const title = extractTitle(section);
const description = extractDescription(section);
const { days, usd } = parseNumbers(textContent);
const coupon = extractCouponCode(textContent);
const expiry = extractExpiryDate(textContent);
const originalPrice = extractOriginalPrice(section);
const discountPercentage = originalPrice && usd ?
Math.round((1 - usd / originalPrice) * 100) : undefined;

// Extract features
const features = extractFeatures(section);

// Extract limitations
const limitations = extractLimitations(section);

// Extract target audience
const targetAudience = extractTargetAudience(section);

// Extract popularity indicators
const popularity = extractPopularity(section);

// Only add if we have some value
if (days || usd || coupon) {
offers.push({
provider: source.name,
category: source.category,
title,
description,
trialDays: days,
creditUSD: usd,
originalPrice,
discountPercentage,
expiry,
coupon,
url: source.url,
reliability: source.reliability,
popularity,
features,
limitations,
targetAudience,
extractionMethod: 'dom',
scrapedAt: new Date().toISOString()
} as Offer);
}
}

return offers;
}

// Helper functions for extraction
function extractTitle(element: Element): string {
const heading = element.querySelector('h1, h2, h3, h4, .title, .plan-name');
return heading?.textContent?.trim() || '';
}

function extractDescription(element: Element): string {
const descElement = element.querySelector('.description, .details, p, .features');
return descElement?.textContent?.trim()?.substring(0, 200) || '';
}

function parseNumbers(text: string): { days?: number; usd?: number } {
const daysMatch = text.match(/(\d+)\s*day/i);
const usdMatch = text.match(/\$?(\d+)\s*(?:usd|credits?|credit)/i);
return {
days: daysMatch ? parseInt(daysMatch[1], 10) : undefined,
usd: usdMatch ? parseInt(usdMatch[1], 10) : undefined,
};
}

function extractCouponCode(text: string): string | undefined {
const couponMatch = text.match(/code[:\s]*([A-Z0-9_-]{5,})/i);
return couponMatch ? couponMatch[1] : undefined;
}

function extractExpiryDate(text: string): string | undefined {
const dateMatch = text.match(/expires?\s*[:\s]*([A-Za-z0-9, ]{5,})/i);
if (!dateMatch) return undefined;

const date = new Date(dateMatch[1]);
return isNaN(date.getTime()) ? undefined : date.toISOString();
}

function extractOriginalPrice(element: Element): number | undefined {
const priceElement = element.querySelector('.original-price, .was-price, .regular-price, del');
if (!priceElement) return undefined;

const priceText = priceElement.textContent || '';
const priceMatch = priceText.match(/\$?(\d+(?:\.\d+)?)/);
return priceMatch ? parseFloat(priceMatch[1]) : undefined;
}

function extractFeatures(element: Element): string[] | undefined {
const featuresElement = element.querySelector('.features, .includes, ul.features');
if (!featuresElement) return undefined;

const featureItems = featuresElement.querySelectorAll('li');
const features = [];

for (const item of featureItems) {
const text = item.textContent?.trim();
if (text) features.push(text);
}

return features.length > 0 ? features : undefined;
}

function extractLimitations(element: Element): string[] | undefined {
const limitationsElement = element.querySelector('.limitations, .restrictions, ul.limitations');
if (!limitationsElement) return undefined;

const limitationItems = limitationsElement.querySelectorAll('li');
const limitations = [];

for (const item of limitationItems) {
const text = item.textContent?.trim();
if (text) limitations.push(text);
}

return limitations.length > 0 ? limitations : undefined;
}

function extractTargetAudience(element: Element): string[] | undefined {
const audienceElement = element.querySelector('.audience, .target, .for');
if (!audienceElement) return undefined;

const text = audienceElement.textContent || '';
const audienceMatch = text.match(/for\s+([^,.]+)/i);

if (audienceMatch) {
return audienceMatch[1].split(/\s+and\s+|\s*,\s*/).map(a => a.trim());
}

return undefined;
}

function extractPopularity(element: Element): number | undefined {
const popularityElement = element.querySelector('.upvotes, .likes, .stars, .points');
if (!popularityElement) return undefined;

const text = popularityElement.textContent || '';
const match = text.match(/(\d+)/);
return match ? parseInt(match[1], 10) : undefined;
}

function generateOfferId(offer: Offer): string {
// Create a deterministic ID based on key attributes
const key = `${offer.provider}-${offer.title}-${offer.coupon || 'no-coupon'}`;
return Buffer.from(key).toString('base64').replace(/[^a-zA-Z0-9]/g, '').substring(0, 16);
}

// Cache management
async function loadCache(): Promise<Map<any, any>> {
try {
const cached = await redis.get('dealHistory');
return cached ? new Map(JSON.parse(cached)) : new Map();
} catch (error) {
console.error('Failed to load cache:', error);
return new Map();
}
}

async function saveCache(cache: Map<any, any>) {
try {
await redis.setex('dealHistory', CONFIG.CACHE_TTL_HOURS * 3600, JSON.stringify([...cache]));
} catch (error) {
console.error('Failed to save cache:', error);
}
}

// Parallel scraping with worker pool
async function scrapeAllSources(): Promise<any[]> {
const allOffers: Offer[] = [];
const cache = await loadCache();

// Process sources in parallel batches
for (let i = 0; i < SOURCES.length; i += CONFIG.PARALLEL_SCRAPES) {
const batch = SOURCES.slice(i, i + CONFIG.PARALLEL_SCRAPES);

const promises = batch.map(async (source, index) => {
return new Promise<any[]>((resolve) => {
const worker = workerPool[index % workerPool.length];

worker.once('message', (result) => {
if (result.success) {
// Enrich offers with metadata
const enrichedOffers = result.offers.map((offer: Offer) => {
offer.id = generateOfferId(offer);
offer.source = source.name;
offer.reliability = source.reliability;
offer.extractionMethod = source.extractionMethod;
offer.scrapedAt = new Date().toISOString();

// Check if we've seen this deal before
const history = cache.get(offer.id);
if (history) {
offer.occurrenceCount = history.occurrenceCount + 1;
// Update price history if price changed
if (offer.originalPrice && !history.priceHistory.find((p: { price: number | undefined; }) => p.price === offer.originalPrice)) {
history.priceHistory.push({
price: offer.originalPrice,
date: new Date().toISOString()
});
}
// Check if deal is trending (increasing popularity)
offer.trending = offer.popularity && history.averageScore &&
offer.popularity > history.averageScore * 1.2;
} else {
offer.occurrenceCount = 1;
offer.trending = false;
}

// Calculate score
offer.score = computeScore(offer);

return offer;
});

resolve(enrichedOffers);
} else {
console.error(`⚠️ Failed to scrape ${result.source}:`, result.error);
resolve([]);
}
});

worker.postMessage(source);
});
});

const batchResults = await Promise.all(promises);
allOffers.push(...batchResults.flat());

// Brief pause between batches to avoid rate limiting
if (i + CONFIG.PARALLEL_SCRAPES < SOURCES.length) {
await new Promise(resolve => setTimeout(resolve, 2000));
}
}

return allOffers;
}

// Main entry point
export async function runUltimateDealHunter() {
console.log('🚀 Starting Ultimate AI Deal Hunter...');

// Scrape all sources in parallel
const allOffers = await scrapeAllSources();

// Deduplicate offers
const deduplicatedOffers = await deduplicateOffers(allOffers);

// Score and rank
const top = deduplicatedOffers
.sort((a, b) => b.score - a.score)
.slice(0, CONFIG.MAX_RESULTS);

// Save to Redis for dashboard
await redis.setex('deals:latest', CONFIG.CACHE_TTL_HOURS * 3600, JSON.stringify(top));

// Send notifications
await sendNotifications(top);

// Update cache
const cache = await loadCache();
for (const offer of top) {
const history = cache.get(offer.id);
if (history) {
history.lastSeen = new Date().toISOString();
history.occurrenceCount += 1;
history.averageScore = (history.averageScore * (history.occurrenceCount - 1) + offer.score) / history.occurrenceCount;
} else {
cache.set(offer.id, {
dealId: offer.id,
firstSeen: new Date().toISOString(),
lastSeen: new Date().toISOString(),
priceHistory: offer.originalPrice ? [{
price: offer.originalPrice,
date: new Date().toISOString()
}] : [],
occurrenceCount: 1,
averageScore: offer.score,
trending: false
});
}
}
await saveCache(cache);

console.log(`✅ Found ${allOffers.length} offers, deduplicated to ${deduplicatedOffers.length}, top ${top.length} sent to notifications`);

return top;
}

// Deduplicate offers based on similarity
async function deduplicateOffers(offers: Offer[]): Promise<any[]> {
const deduplicated: Offer[] = [];
const seenIds = new Set<string>();

for (const offer of offers) {
if (!seenIds.has(offer.id)) {
seenIds.add(offer.id);
deduplicatedOffers.push(offer);
}
}

return deduplicatedOffers;
}

// Send notifications to multiple channels
async function sendNotifications(offers: Offer[]) {
const top3 = offers.slice(0, 3);

// Send to Slack
if (CONFIG.NOTIFICATION_CHANNELS.slack) {
await sendSlackNotification(top3);
}

// Send to Discord
if (CONFIG.NOTIFICATION_CHANNELS.discord) {
await sendDiscordNotification(top3);
}

// Send email summary
if (CONFIG.NOTIFICATION_CHANNELS.email) {
await sendEmailNotification(offers);
}

// Send SMS for urgent deals
const urgentDeals = offers.filter(offer => {
if (!offer.expiry) return false;
const daysUntilExpiry = (new Date(offer.expiry).getTime() - Date.now()) / (1000 * 60 * 60 * 24);
return daysUntilExpiry < 3 && offer.score > 50;
});

if (urgentDeals.length > 0 && CONFIG.NOTIFICATION_CHANNELS.sms) {
await sendSMSNotification(urgentDeals);
}

// Send to generic webhook
if (CONFIG.NOTIFICATION_CHANNELS.webhook) {
await sendWebhookNotification(top3);
}
}

// Slack notification
async function sendSlackNotification(offers: Offer[]) {
const blocks = offers.map(o => ({
type: 'section',
text: {
type: 'mrkdwn',
text: `*${o.title}* – ${o.provider}\n${o.description}\n` +
`${o.trialDays ? `🗓️ ${o.trialDays}-day trial` : ''}` +
`${o.creditUSD ? `💰 $${o.creditUSD} credit` : ''}` +
`${o.discountPercentage ? `🏷️ ${o.discountPercentage}% off` : ''}` +
`${o.coupon ? `🔑 Code: \`${o.coupon}\`` : ''}` +
`${o.expiry ? `⏰ Expires: ${formatISO(new Date(o.expiry))}` : ''}` +
`${o.trending ? '🔥 Trending!' : ''}\n` +
`<${o.url}|🔗 View Deal>`,
},
}));

const payload = {
text: '🚀 Today\'s top AI-tool free trials & discounts',
blocks,
};

await fetch(CONFIG.NOTIFICATION_CHANNELS.slack as RequestInfo, {
method: 'POST',
headers: { 'Content-Type': 'application/json' },
body: JSON.stringify(payload),
});
}

// Discord notification
async function sendDiscordNotification(offers: Offer[]) {
const embeds = offers.map(o => ({
title: o.title,
description: o.description,
url: o.url,
color: o.trending ? 0xFF4500 : 0x00AE86, // Orange for trending, green for regular
fields: [
...(o.trialDays ? [{ name: 'Trial Period', value: `${o.trialDays} days`, inline: true }] : []),
...(o.creditUSD ? [{ name: 'Free Credits', value: `$${o.creditUSD}`, inline: true }] : []),
...(o.discountPercentage ? [{ name: 'Discount', value: `${o.discountPercentage}%`, inline: true }] : []),
...(o.coupon ? [{ name: 'Coupon Code', value: `\`${o.coupon}\``, inline: true }] : []),
...(o.expiry ? [{ name: 'Expires', value: formatISO(new Date(o.expiry)), inline: true }] : []),
...(o.popularity ? [{ name: 'Popularity', value: o.popularity.toString(), inline: true }] : [])
].filter(Boolean),
footer: { text: `${o.provider} • Score: ${o.score.toFixed(1)}` }
}));

const payload = {
content: '🚀 Today\'s top AI-tool free trials & discounts',
embeds
};

await fetch(CONFIG.NOTIFICATION_CHANNELS.discord as RequestInfo, {
method: 'POST',
headers: { 'Content-Type': 'application/json' },
body: JSON.stringify(payload),
});
}

// Email notification
async function sendEmailNotification(offers: Offer[]) {
const html = `

🚀 Today's AI Tool Deals

${offers.map(o => `



${o.title} - ${o.provider}


${o.description}



${o.trialDays ? `
🗓️ ${o.trialDays}-day trial` : ''}

${o.creditUSD ? `
💰 $${o.creditUSD} credit` : ''}

${o.discountPercentage ? `
🏷️ ${o.discountPercentage}% off` : ''}

${o.coupon ? `
🔑 Code: ${o.coupon}` : ''}

${o.expiry ? `
⏰ Expires: ${formatISO(new Date(o.expiry))}` : ''}

${o.trending ? `
🔥 Trending deal!` : ''}




View Deal



`).join('')}
`;

const payload = {
to: process.env.EMAIL_RECIPIENTS?.split(',') || [],
subject: '🚀 Today\'s AI Tool Deals',
html
};

await fetch(CONFIG.NOTIFICATION_CHANNELS.email as RequestInfo, {
method: 'POST',
headers: { 'Content-Type': 'application/json' },
body: JSON.stringify(payload),
});
}

// SMS notification for urgent deals
async function sendSMSNotification(offers: Offer[]) {
const message = `🚀 URGENT AI DEALS EXPIRING SOON:\n` +
offers.map(o => `${o.title} (${o.provider}): ${o.coupon ? `Code: ${o.coupon}` : `${o.creditUSD ? `$${o.creditUSD} credit` : `${o.trialDays} days trial`}`}`).join('\n');

const payload = {
to: process.env.SMS_RECIPIENTS?.split(',') || [],
message
};

await fetch(CONFIG.NOTIFICATION_CHANNELS.sms as RequestInfo, {
method: 'POST',
headers: { 'Content-Type': 'application/json' },
body: JSON.stringify(payload),
});
}

// Generic webhook notification
async function sendWebhookNotification(offers: Offer[]) {
const payload = {
title: 'AI Tool Deals',
deals: offers.map(o => ({
title: o.title,
provider: o.provider,
category: o.category,
description: o.description,
trialDays: o.trialDays,
creditUSD: o.creditUSD,
discountPercentage: o.discountPercentage,
coupon: o.coupon,
expiry: o.expiry,
url: o.url,
score: o.score,
trending: o.trending,
popularity: o.popularity
}))
};

await fetch(CONFIG.NOTIFICATION_CHANNELS.webhook as RequestInfo, {
method: 'POST',
headers: { 'Content-Type': 'application/json' },
body: JSON.stringify(payload),
});
}

// If run directly
if (require.main === module) {
runUltimateDealHunter()
.then(() => console.log('✅ Ultimate deal report sent'))
.catch(err => console.error('❌ Ultimate deal hunter failed', err));
}
