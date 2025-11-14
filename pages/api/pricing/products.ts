import type { NextApiRequest, NextApiResponse } from 'next';
import { pricingTiers } from './check';

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const products = Object.entries(pricingTiers).map(([id, tier]) => ({
      id,
      ...tier,
      priceId: process.env[`STRIPE_PRICE_${id.toUpperCase()}`],
      checkoutUrl: `/api/checkout/create?plan=${id}`
    }));

    res.json({ products });
  } catch (error) {
    console.error('Get products error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
}
