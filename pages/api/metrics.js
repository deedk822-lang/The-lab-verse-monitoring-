import { register, collectDefaultMetrics } from 'prom-client';

collectDefaultMetrics();

export default async function handler(req, res) {
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    res.setHeader('Content-Type', register.contentType);
    res.send(await register.metrics());
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
}
