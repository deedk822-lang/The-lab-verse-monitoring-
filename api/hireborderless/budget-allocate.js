import { MODEL_CATALOG } from '../../models.config.js';

export default async function handler(req, res) {
  const { location, monthly_budget_zar } = req.body;

  // HRGPT optimizes spend across models and humans
  try {
    const allocation = await fetch('https://api.hireborderless.com/v1/budget/optimize', {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${process.env.HIREBORDERLESS_API_KEY}` },
      body: JSON.stringify({
        total_budget: monthly_budget_zar,
        constraints: {
          'Sebokeng': { min_localai_hours: 500, max_cloud_spend: 50 }, // R50/month cloud
          'Three Rivers': { min_cloud_ai_quality: 8.5 }, // Only premium models
          'Vanderbijlpark': { max_avg_cost_per_query: 0.001 } // Ultra-cheap
        },
        model_catalog: MODEL_CATALOG
      })
    });

    if (!allocation.ok) {
      const errorText = await allocation.text();
      throw new Error(`API call failed with status ${allocation.status}: ${errorText}`);
    }

    const budgetPlan = await allocation.json();
    res.json(budgetPlan);
  } catch (error) {
    console.error('Failed to allocate budget:', error);
    res.status(500).json({ error: 'Internal server error during budget allocation.' });
  }
}
