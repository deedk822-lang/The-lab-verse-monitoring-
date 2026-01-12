import type { NextApiRequest, NextApiResponse } from 'next';
import { getTenantConfig, updateTenantBilling } from '@/lib/multitenancy';
import Stripe from 'stripe';

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
    // Get tenant configuration from hostname
    const hostname = req.headers.host || '';
    const tenant = await getTenantConfig(hostname);

    if (!tenant) {
      return res.status(404).json({ error: 'Tenant not found' });
    }

    const { model, messages, temperature = 0.7 } = req.body;

    // Validate model access
    if (!tenant.settings.allowedModels.includes('all') &&
        !tenant.settings.allowedModels.includes(model)) {
      return res.status(403).json({
        error: 'Model not available',
        allowedModels: tenant.settings.allowedModels
      });
    }

    // Process the request (simplified)
    const response = await processAIRequest({
      model,
      messages,
      temperature,
      apiKeys: tenant.apiKeys
    });

    // Track usage for billing
    if (tenant.billing.plan === 'white_label') {
      // Bill the white-label agency
      if (tenant.billing.stripeItemId) {
        await stripe.subscriptionItems.createUsageRecord(
          tenant.billing.stripeItemId,
          {
            quantity: 1,
            timestamp: Math.floor(Date.now() / 1000),
            action: 'increment'
          }
        );
      }

      // Update tenant billing
      await updateTenantBilling(tenant.id, { requests: 1, model });
    }

    // Return response with tenant branding
    res.json({
      ...response,
      tenant: tenant.name,
      branding: {
        name: tenant.theme.brandName,
        logo: tenant.logoUrl
      }
    });

  } catch (error) {
    console.error('Gateway error:', error);
    res.status(500).json({
      error: 'Request failed',
      message: error instanceof Error ? error.message : 'Unknown error'
    });
  }
}

async function processAIRequest(params: {
  model: string;
  messages: any[];
  temperature: number;
  apiKeys: any;
}): Promise<any> {
  // Simplified AI processing
  // In production, route to appropriate AI provider
  return {
    id: 'chatcmpl-' + Math.random().toString(36),
    object: 'chat.completion',
    created: Math.floor(Date.now() / 1000),
    model: params.model,
    choices: [{
      index: 0,
      message: {
        role: 'assistant',
        content: 'This is a sample response from the multi-tenant gateway.'
      },
      finish_reason: 'stop'
    }],
    usage: {
      prompt_tokens: 10,
      completion_tokens: 20,
      total_tokens: 30
    }
  };
}
