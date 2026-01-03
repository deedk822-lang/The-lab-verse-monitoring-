/**
 * Secure Framer API Proxy
 * FIXED: SSRF vulnerability using strict hostname validation
 */

// Whitelist of allowed API domains
const ALLOWED_HOSTS = [
  'api.hubspot.com',
  'api.mailchimp.com',
  'api.thelabverse.com'
];

export default async function handler(req, res) {
  // Only allow POST requests
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  // Extract endpoint from body or query params (Framer flexibility)
  const endpoint = req.body?.endpoint || req.query?.endpoint;

  if (!endpoint) {
    return res.status(400).json({
      error: 'Missing endpoint parameter',
      hint: 'Provide endpoint in request body or query string'
    });
  }

  // CRITICAL FIX: Use URL parsing for strict validation
  let targetUrl;
  try {
    targetUrl = new URL(endpoint);
  } catch (error) {
    return res.status(400).json({
      error: 'Invalid URL format',
      details: error.message
    });
  }

  // CRITICAL FIX: Check hostname strictly (prevents SSRF bypass)
  if (!ALLOWED_HOSTS.includes(targetUrl.hostname)) {
    return res.status(403).json({
      error: 'Domain not allowed',
      allowed: ALLOWED_HOSTS,
      attempted: targetUrl.hostname,
      hint: 'Contact admin to whitelist new domains'
    });
  }

  // Validate protocol (prevent file://, data://, etc.)
  if (!['https:', 'http:'].includes(targetUrl.protocol)) {
    return res.status(400).json({
      error: 'Invalid protocol',
      allowed: ['https', 'http'],
      attempted: targetUrl.protocol
    });
  }

  try {
    // Forward request to validated endpoint
    const response = await fetch(targetUrl.href, {
      method: req.body?.method || 'GET',
      headers: {
        'Content-Type': 'application/json',
        'User-Agent': 'Framer-Proxy/1.0',
        // Forward authorization if provided
        ...(req.body?.headers || {})
      },
      body: req.body?.data ? JSON.stringify(req.body.data) : undefined,
      // Add timeout to prevent hanging
      signal: AbortSignal.timeout(10000) // 10 second timeout
    });

    const data = await response.json();

    // Return response with appropriate status
    return res.status(response.status).json(data);

  } catch (error) {
    console.error('Proxy error:', error);

    // Don't expose internal error details
    return res.status(500).json({
      error: 'Proxy request failed',
      timestamp: new Date().toISOString()
    });
  }
}
