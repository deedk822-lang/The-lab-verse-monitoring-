import type { NextApiRequest, NextApiResponse } from 'next';
import Stripe from 'stripe';

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!, {
  apiVersion: '2024-11-20.acacia',
});

export interface PricingTier {
  name: string;
  price: number;
  requests: number | 'unlimited';
  models: string[];
  features: string[];
}

export const pricingTiers: Record<string, PricingTier> = {
  starter: {
    name: 'Starter',
    price: 29,
    requests: 1000,
    models: ['basic', 'hf-small'],
    features: [
      '1,000 API requests/month',
      'Basic models',
      'Email support',
      'Community access'
    ]
  },
  pro: {
    name: 'Professional',
    price: 99,
    requests: 10000,
    models: ['advanced', 'basic', 'hf-large'],
    features: [
      '10,000 API requests/month',
      'Advanced models',
      'Priority support',
      'Slack integration',
      'Custom webhooks'
    ]
  },
  enterprise: {
    name: 'Enterprise',
    price: 299,
    requests: 'unlimited',
    models: ['all'],
    features: [
      'Unlimited API requests',
      'All models including GPT-4',
      '24/7 phone support',
      'Dedicated account manager',
      'Custom integrations',
      'SLA guarantee',
      'White-label option'
    ]
  }
};

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const { userId, usage } = req.body;

    if (!userId) {
      return res.status(400).json({ error: 'userId required' });
    }

    // Get user's subscription from Stripe
    const subscriptions = await stripe.subscriptions.list({
      customer: userId,
      status: 'active',
      limit: 1
    });

    if (subscriptions.data.length === 0) {
      return res.status(403).json({ 
        error: 'No active subscription',
        upgradeUrl: '/pricing'
      });
    }

    const subscription = subscriptions.data[0];
    const planId = subscription.items.data[0].price.lookup_key || 'starter';
    const tier = pricingTiers[planId];

    if (!tier) {
      return res.status(500).json({ error: 'Invalid pricing tier' });
    }

    // Check rate limits
    if (tier.requests !== 'unlimited' && usage.requests > tier.requests) {
      return res.status(429).json({ 
        error: 'Rate limit exceeded',
        limit: tier.requests,
        used: usage.requests,
        upgradeUrl: '/pricing?upgrade=true'
      });
    }

    // Check model access
    if (!tier.models.includes('all') && !tier.models.includes(usage.model)) {
      return res.status(403).json({ 
        error: 'Model not available in your plan',
        availableModels: tier.models,
        requestedModel: usage.model,
        upgradeUrl: '/pricing?model=' + usage.model
      });
    }

    res.json({ 
      allowed: true, 
      tier: tier.name,
      remaining: tier.requests === 'unlimited' 
        ? 'unlimited' 
        : tier.requests - usage.requests,
      resetDate: subscription.current_period_end * 1000
    });

  } catch (error) {
    console.error('Pricing check error:', error);
    res.status(500).json({ 
      error: 'Internal server error',
      message: error instanceof Error ? error.message : 'Unknown error'
    });
  }
}
