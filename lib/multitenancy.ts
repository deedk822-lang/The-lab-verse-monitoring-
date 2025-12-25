export interface TenantConfig {
  id: string;
  name: string;
  customDomain?: string;
  logoUrl?: string;
  theme: {
    primaryColor: string;
    secondaryColor: string;
    brandName: string;
  };
  apiKeys: {
    huggingface?: string;
    socialpilot?: string;
    unito?: string;
    wordpress?: string;
  };
  billing: {
    plan: 'white_label' | 'enterprise' | 'pro' | 'starter';
    stripeCustomerId: string;
    stripeItemId?: string;
    monthlyRevenue: number;
    revenueShare: number; // 0.3 for white_label = 30% to platform
  };
  settings: {
    allowedModels: string[];
    rateLimit: number;
    features: string[];
  };
}

const tenants: Map<string, TenantConfig> = new Map();

export async function getTenantConfig(hostname: string): Promise<TenantConfig | null> {
  // Check cache first
  if (tenants.has(hostname)) {
    return tenants.get(hostname)!;
  }

  // In production, fetch from database
  // For now, use environment-based config

  // Default tenant for main domain
  if (hostname === process.env.BASE_URL?.replace('https://', '')) {
    return {
      id: 'default',
      name: 'Lab Verse Monitoring',
      theme: {
        primaryColor: '#0070f3',
        secondaryColor: '#ff4081',
        brandName: 'Lab Verse'
      },
      apiKeys: {
        huggingface: process.env.HUGGINGFACE_API_KEY,
        socialpilot: process.env.SOCIALPILOT_API_KEY,
        unito: process.env.UNITO_API_KEY,
        wordpress: process.env.WORDPRESS_API_KEY
      },
      billing: {
        plan: 'enterprise',
        stripeCustomerId: '',
        monthlyRevenue: 0,
        revenueShare: 0
      },
      settings: {
        allowedModels: ['all'],
        rateLimit: 100000,
        features: ['all']
      }
    };
  }

  // Check for custom domain tenants
  // This would normally query your database
  // const tenant = await db.tenant.findUnique({ where: { customDomain: hostname }});

  return null;
}

export async function createTenant(config: Partial<TenantConfig>): Promise<TenantConfig> {
  const tenant: TenantConfig = {
    id: config.id || Math.random().toString(36).substring(7),
    name: config.name || 'New Tenant',
    customDomain: config.customDomain,
    logoUrl: config.logoUrl,
    theme: config.theme || {
      primaryColor: '#0070f3',
      secondaryColor: '#ff4081',
      brandName: config.name || 'Gateway'
    },
    apiKeys: config.apiKeys || {},
    billing: config.billing || {
      plan: 'white_label',
      stripeCustomerId: '',
      monthlyRevenue: 0,
      revenueShare: 0.3
    },
    settings: config.settings || {
      allowedModels: ['basic', 'advanced'],
      rateLimit: 10000,
      features: ['api', 'webhooks']
    }
  };

  // In production, save to database
  // await db.tenant.create({ data: tenant });

  // Cache it
  if (tenant.customDomain) {
    tenants.set(tenant.customDomain, tenant);
  }

  return tenant;
}

export async function updateTenantBilling(
  tenantId: string,
  usage: { requests: number; model: string }
): Promise<void> {
  // Calculate costs
  const costPerRequest = 0.001; // $0.001 per request
  const cost = usage.requests * costPerRequest;

  // In production, update database
  // await db.tenant.update({
  //   where: { id: tenantId },
  //   data: {
  //     monthlyRevenue: { increment: cost },
  //     lastBilledAt: new Date()
  //   }
  // });

  console.log(`Billed tenant ${tenantId}: $${cost.toFixed(2)}`);
}

export function calculateRevenueShare(tenant: TenantConfig): {
  platformRevenue: number;
  tenantRevenue: number;
} {
  const platformRevenue = tenant.billing.monthlyRevenue * tenant.billing.revenueShare;
  const tenantRevenue = tenant.billing.monthlyRevenue * (1 - tenant.billing.revenueShare);

  return { platformRevenue, tenantRevenue };
}
