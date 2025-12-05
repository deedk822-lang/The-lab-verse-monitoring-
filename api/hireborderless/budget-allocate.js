import { MODEL_CATALOG } from '../../models.config.js';

export default async function handler(req, res) {
  const { location, monthly_budget_zar } = req.body;

  // HRGPT optimizes spend across models and humans
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

  const budgetPlan = await allocation.json();

  // Example output:
  // {
  //   location: 'Sebokeng',
  //   total_budget: 5000,
  //   allocated_to: {
  //     'mistral-7b-instruct-v0.2-q4': { hours: 720, cost: 0 }, // Runs 24/7 on Pi
  //     'hireborderless_instructors': { headcount: 5, cost: 42500 },
  //     'mixtral-8x7b-together': { tokens: 83333, cost: 50 } // R50 cloud backup
  //   }
  // }

  res.json(budgetPlan);
}
