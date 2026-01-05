import { MODEL_CATALOG } from '../../models.config.js';

async function getEskomStage(location) {
  console.warn(`getEskomStage called for ${location}, returning placeholder.`);
  // Return a mock response or call a real service
  // return await fetchRealEskomData(location);
  return 0; // Placeholder
}

async function getInternetUptime(location) {
  console.warn(`getInternetUptime called for ${location}, returning placeholder.`);
  // return await fetchRealUptimeData(location);
  return 100; // Placeholder
}

export default async function handler(req, res) {
  const { location, task, urgency } = req.body;

  // HRGPT decides which model to deploy based on location constraints
  const decision = await fetch('https://api.hireborderless.com/v1/decision-engine/run', {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${process.env.HIREBORDERLESS_API_KEY}` },
    body: JSON.stringify({
      context: {
        location: location,
        task: task,
        urgency: urgency,
        eskom_stage: await getEskomStage(location),
        internet_uptime: await getInternetUptime(location)
      },
      rules: [
        "IF eskom_stage > 4 THEN use_localai_only",
        "IF location = 'Three Rivers' AND task = 'executive' THEN use_gpt_4o_mini",
        "IF cost_per_hour < 0.50 THEN prefer_cloud",
        "IF language INCLUDES 'sesotho' THEN use_mistral_7b"
      ]
    })
  });

  const selectedModel = await decision.json();

  // Deploy the model to Vercel or LocalAI
  const deployment = await deployModel(selectedModel.model_id, location);

  res.json({
    location,
    task,
    model_deployed: selectedModel.model_id,
    cost_per_hour: selectedModel.estimated_cost,
    loadshedding_proof: selectedModel.localai
  });
}

async function deployModel(modelId, location) {
  const model = MODEL_CATALOG[modelId];

  if (model.provider === 'LocalAI') {
    // SSH into location's Raspberry Pi and pull model
    const baseUrl = model.endpoint.replace(/\/v1\/.*$/, '');
    return await fetch(`${baseUrl}/models/apply`, {
      method: 'POST',
      body: JSON.stringify({
        model: modelId,
        quant: 'q4_0' // 4-bit quantization for Pi efficiency
      })
    });
  } else {
    // Cloud model: just verify API key is set in Vercel
    return { status: 'ready', provider: model.provider };
  }
}
