// pages/api/deals/refresh.ts
import { NextApiRequest, NextApiResponse } from 'next';
import { Redis } from 'ioredis';

const redis = new Redis(process.env.REDIS_URL || 'redis://localhost:6379');

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
if (req.method !== 'POST') {
return res.status(405).json({ error: 'Method not allowed' });
}

try {
// Trigger a refresh by setting a flag
await redis.set('deal-refresh-trigger', Date.now());

// Notify all connected clients
await redis.publish('deal-updates', JSON.stringify({
type: 'refresh-started',
timestamp: new Date().toISOString()
}));

res.status(200).json({ success: true, message: 'Deal refresh triggered' });
} catch (error) {
console.error('Failed to trigger deal refresh:', error);
res.status(500).json({ error: 'Failed to trigger deal refresh' });
}
}
