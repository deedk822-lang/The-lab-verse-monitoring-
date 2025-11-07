import crypto from 'crypto';

/**
* Verifies the webhook signature from RankYak.
* @param {string} payload - The raw request body.
* @param {string} signature - The value of the 'x-webhook-signature' header.
* @param {string} secret - The webhook secret.
* @returns {boolean} - True if the signature is valid, false otherwise.
*/
function verifySignature(payload, signature, secret) {
  if (!signature || !secret) return false;

  const hmac = crypto.createHmac('sha256', secret);
  const digest = 'sha256=' + hmac.update(payload).digest('hex');

  try {
    // Use a Buffer-based comparison for security
    return crypto.timingSafeEqual(
      Buffer.from(signature),
      Buffer.from(digest)
    );
  } catch (error) {
    console.error('Error during signature verification:', error);
    return false;
  }
}

// Export as a mutable object to allow for easier mocking in tests
const utils = {
  verifySignature,
};

export default utils;
