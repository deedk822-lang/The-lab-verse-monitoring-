// pages/api/deals/stream.ts
import { NextApiRequest, NextApiResponse } from 'next';
import { Redis } from 'ioredis';

const redis = new Redis(process.env.REDIS_URL || 'redis://localhost:6379');

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
if (req.method !== 'GET') {
return res.status(405).json({ error: 'Method not allowed' });
}

// Set up SSE
res.writeHead(200, {
'Content-Type': 'text/event-stream',
'Cache-Control': 'no-cache',
'Connection': 'keep-alive',
});

// Send initial data
const cachedDeals = await redis.get('deals:latest');
if (cachedDeals) {
res.write(`data: ${JSON.stringify({ type: 'deals', data: JSON.parse(cachedDeals) })}\n\n`);
}

// Subscribe to Redis updates
const subscriber = redis.duplicate();
await subscriber.subscribe('deal-updates');

subscriber.on('message', (channel, message) => {
if (channel === 'deal-updates') {
res.write(`data: ${JSON.stringify({ type: 'update', data: JSON.parse(message) })}\n\n`);
}
});

// Clean up on disconnect
req.on('close', () => {
subscriber.disconnect();
});
}
