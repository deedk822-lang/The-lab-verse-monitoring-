import type { NextApiRequest, NextApiResponse } from 'next';
import Stripe from 'stripe';
import { pricingTiers } from '../pricing/check';

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!, {
  apiVersion: '2024-11-20.acacia',
});

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const { plan, email, userId } = req.body;

    if (!plan || !email) {
      return res.status(400).json({ error: 'plan and email required' });
    }

    const tier = pricingTiers[plan];
    if (!tier) {
      return res.status(400).json({ error: 'Invalid plan' });
    }

    // Create or retrieve customer
    let customer;
    if (userId) {
      const customers = await stripe.customers.list({ email, limit: 1 });
      customer = customers.data[0];
    }
    
    if (!customer) {
      customer = await stripe.customers.create({
        email,
        metadata: { userId: userId || 'new' }
      });
    }

    // Create checkout session
    const session = await stripe.checkout.sessions.create({
      customer: customer.id,
      line_items: [
        {
          price_data: {
            currency: 'usd',
            product_data: {
              name: `${tier.name} Plan`,
              description: tier.features.join(', ')
            },
            unit_amount: tier.price * 100, // Convert to cents
            recurring: {
              interval: 'month'
            }
          },
          quantity: 1
        }
      ],
      mode: 'subscription',
      success_url: `${process.env.BASE_URL}/success?session_id={CHECKOUT_SESSION_ID}`,
      cancel_url: `${process.env.BASE_URL}/pricing`,
      metadata: {
        plan,
        userId: userId || customer.id
      }
    });

    res.json({ 
      checkoutUrl: session.url,
      sessionId: session.id
    });

  } catch (error) {
    console.error('Checkout creation error:', error);
    res.status(500).json({ 
      error: 'Checkout creation failed',
      message: error instanceof Error ? error.message : 'Unknown error'
    });
  }
}
