const ALLOWED_HOSTS = [
  'api.hubspot.com',
  'api.mailchimp.com'
];

export default async function handler(req, res) {
  const { endpoint } = req.body;

  try {
    const url = new URL(endpoint);
    if (!ALLOWED_HOSTS.includes(url.hostname)) {
      return res.status(403).json({ error: 'Domain not allowed' });
    }
  } catch (error) {
    return res.status(400).json({ error: 'Invalid URL' });
  }

  const response = await fetch(url.href, {
    method: req.body?.method || 'GET',
    headers: req.body?.headers || {},
    body: req.body?.data ? JSON.stringify(req.body.data) : undefined,
    signal: AbortSignal.timeout(10000)
  });

  return res.status(response.status).json(await response.json());
}