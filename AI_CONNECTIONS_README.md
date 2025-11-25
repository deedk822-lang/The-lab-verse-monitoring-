┌─────────────────────────────────────────────────┐
│         Intelligent Router API                   │
│  /api/ai/intelligent-router?action=...          │
└─────────────────┬───────────────────────────────┘
                  │
        ┌─────────┴─────────┐
        │                   │
   ┌────▼────┐       ┌─────▼──────┐
   │ Generate│       │ Fact-Check │
   │ Content │       │   Claims   │
   └────┬────┘       └─────┬──────┘
        │                  │
   ┌────▼────────┐    ┌───▼──────────────┐
   │  Primary    │    │  3 Judge Agents  │
   │  (Mistral)  │    │  (Parallel Exec) │
   └────┬────────┘    └───┬──────────────┘
        │                  │
   ┌────▼────────┐    ┌───▼──────────────┐
   │  Fallback   │    │  Consensus       │
   │  (GLM-4)    │    │  Protocol        │
   └─────────────┘    └───┬──────────────┘
                           │
                      ┌────▼─────────┐
                      │  Evidence    │
                      │  Block       │
                      └──────────────┘ API Endpoints

1. Simple Generation with Fallback

Endpoint: POST /api/ai/intelligent-router?action=generate

Request:

JSON


{
  "prompt": "Explain quantum computing",
  "primaryModel": "mixtral-8x22b-instruct",
  "fallbackModel": "glm-4"
}


Response:

JSON


{
  "success": true,
  "content": "Quantum computing is...",
  "modelUsed": "mixtral-8x22b-instruct",
  "timestamp": "2025-11-23T02:55:00Z"
}


2. Generation with Fact-Checking

Endpoint: POST /api/ai/intelligent-router?action=generate-with-fact-check

Request:

JSON


{
  "prompt": "Write about the global AI market size in 2030",
  "enableFactCheck": true
}


Response:

JSON


{
  "success": true,
  "content": "The global AI market... [with evidence blocks appended]",
  "modelUsed": "mixtral-8x22b-instruct",
  "factChecks": [
    {
      "claim": "The global AI market is projected to reach $826B by 2030",
      "finalVerdict": "Fact-Checked: True",
      "consensus": "Consensus: 2/3 judges agree",
      "judgeResults": [...],
      "evidenceBlock": "### Fact-Check Evidence..."
    }
  ],
  "factCheckCount": 1,
  "timestamp": "2025-11-23T02:55:00Z"
}


3. Standalone Fact-Checking

Endpoint: POST /api/ai/intelligent-router?action=fact-check

Request:

JSON


{
  "claim": "The global AI market is projected to reach $826B by 2030",
  "searchResults": [
    "Source 1: MarketWatch reports...",
    "Source 2: Statista shows..."
  ]
}


Response:

JSON


{
  "success": true,
  "claim": "The global AI market is projected to reach $826B by 2030",
  "finalVerdict": "Fact-Checked: True",
  "consensus": "Consensus: 2/3 judges agree",
  "judgeResults": [
    {
      "claim": "...",
      "verdict": "True",
      "confidence": 85,
      "evidence_url": "https://www.marketwatch.com/...",
      "reasoning": "Multiple credible sources confirm...",
      "judge": "Judge Gemini"
    },
    ...
  ],
  "evidenceBlock": "### Fact-Check Evidence for Claim...",
  "timestamp": "2025-11-23T02:55:00Z"
}


Setup Instructions

1. Environment Variables

Copy .env.local and configure your API keys:

Bash


# Required for core functionality
MISTRAL_API_KEY=your_mistral_api_key
GEMINI_API_KEY=your_gemini_api_key
GROQ_API_KEY=your_groq_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key

# Optional: Fallback model
GLM_API_KEY=your_glm_api_key
GLM_API_ENDPOINT=https://open.bigmodel.cn/api/paas/v4

# Gateway authentication
GATEWAY_API_KEY=your_secure_gateway_key


2. Install Dependencies

Bash


cd /home/ubuntu/The-lab-verse-monitoring-
npm install --ignore-scripts


3. Start Development Server

Bash


npm run dev


The intelligent router will be available at:

•
http://localhost:3000/api/ai/intelligent-router

4. Test the API

Bash


# Test simple generation
curl -X POST http://localhost:3000/api/ai/intelligent-router?action=generate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_gateway_key" \
  -d '{
    "prompt": "Explain AI in simple terms"
  }'

# Test fact-checking
curl -X POST http://localhost:3000/api/ai/intelligent-router?action=fact-check \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_gateway_key" \
  -d '{
    "claim": "The Earth orbits the Sun"
  }'


Integration with Existing System

Airtable Integration

The fact-checked content can be automatically written back to Airtable:

TypeScript


import { generateFactCheckedContent } from './src/ai-connections/intelligent-router';

async function processAirtableRecord(recordId: string, prompt: string  ) {
  // Generate content with fact-checking
  const result = await generateFactCheckedContent(prompt, true);

  // Write back to Airtable
  await updateAirtableRecord(recordId, {
    content: result.content,
    modelUsed: result.modelUsed,
    factCheckCount: result.factChecks?.length || 0,
    verified: result.success
  });
}


MCP Server Integration

Connect to existing MCP servers for data retrieval:

TypeScript

MCP Server Integration

Connect to existing MCP servers for data retrieval:

TypeScript


// Fetch data from HuggingFace MCP
const hfData = await mcpClient.call('huggingface', 'search_models', {
  query: 'text-generation'
});

// Use in fact-checking
const factCheck = await factCheckClaim(
  'HuggingFace has over 100,000 models',
  [JSON.stringify(hfData)]
);


File Structure

Plain Text


The-lab-verse-monitoring-/
├── src/
│   └── ai-connections/
│       ├── mistral-config.ts        # AI model configurations
│       └── intelligent-router.ts    # Core routing logic
├── pages/
│   └── api/
│       └── ai/
│           └── intelligent-router.ts # API endpoint
├── .env.local                        # Environment variables
└── AI_CONNECTIONS_README.md          # This 𝑓𝑖𝑙𝑒
Deployment Options

Option 1: Deploy to Vercel (Recommended)

Step 1: Install Vercel CLI

Bash


npm install -g vercel


Step 2: Navigate to Project

Bash


cd /home/ubuntu/The-lab-verse-monitoring-


Step 3: Configure Environment Variables

Edit .env.local with your API keys:

Bash


# Required API Keys
MISTRAL_API_KEY=your_mistral_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
GROQ_API_KEY=your_groq_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Gateway Authentication
GATEWAY_API_KEY=choose_a_secure_random_key_here

# Optional: Fallback Model
GLM_API_KEY=your_glm_api_key_here
GLM_API_ENDPOINT=https://open.bigmodel.cn/api/paas/v4


Step 4: Deploy to Vercel

Bash


# Login to Vercel
vercel login

# Deploy to production
vercel --prod


Step 5: Add Environment Variables to Vercel

Bash


# Add each environment variable
vercel env add MISTRAL_API_KEY
vercel env add GEMINI_API_KEY
vercel env add GROQ_API_KEY
vercel env add ANTHROPIC_API_KEY
vercel env add GATEWAY_API_KEY

# Optional
vercel env add GLM_API_KEY
vercel env add GLM_API_ENDPOINT


When prompted, paste your API keys.

Step 6: Redeploy with Environment Variables

Bash


vercel --prod


Your deployment will be available at: https://your-project.vercel.app




Option 2: Test Locally First

Step 1: Install Dependencies

Bash


cd /home/ubuntu/The-lab-verse-monitoring-
npm install --ignore-scripts


Step 2: Configure Environment

Edit .env.local with your API keys (see Option 1, Step 3 )

Step 3: Start Development Server

Bash


npm run dev


Server will start at: http://localhost:3000

Step 4: Test the API

Open a new terminal and run:

Bash


node test-ai-connections.js


Or test manually:

Bash


curl -X POST http://localhost:3000/api/ai/intelligent-router?action=generate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_gateway_key" \
  -d '{
    "prompt": "Explain AI in one sentence"
  }'


Step 5: Deploy to Vercel

Once local testing is successful, follow Option 1 to deploy.




🧪 Testing Your Deployment

Test 1: Simple Generation

Bash


curl -X POST https://your-project.vercel.app/api/ai/intelligent-router?action=generate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_gateway_key" \
  -d '{
    "prompt": "What is artificial intelligence?"
  }'


Expected Response:

JSON


{
  "success": true,
  "content": "Artificial intelligence is...",
  "modelUsed": "mixtral-8x22b-instruct",
  "timestamp": "2025-11-23T..."
}


Test 2: Fact-Checking

Bash


curl -X POST https://your-project.vercel.app/api/ai/intelligent-router?action=fact-check \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_gateway_key" \
  -d '{
    "claim": "The Earth orbits the Sun"
  }'


Expected Response:

JSON


{
  "success": true,
  "finalVerdict": "Fact-Checked: True",
  "consensus": "Consensus: 3/3 judges agree",
  "judgeResults": [...],
  "evidenceBlock": "### Fact-Check Evidence..."
}


Test 3: Complete Workflow

Bash


curl -X POST https://your-project.vercel.app/api/ai/intelligent-router?action=generate-with-fact-check \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_gateway_key" \
  -d '{
    "prompt": "Write about the global AI market",
    "enableFactCheck": true
  }'





🔧 Configuration Reference

Required Environment Variables

Variable
Description
Where to Get
MISTRAL_API_KEY
Mistral AI API key
console.mistral.ai
GEMINI_API_KEY
Google Gemini API key
makersuite.google.com
GROQ_API_KEY
Groq API key
console.groq.com
ANTHROPIC_API_KEY
Anthropic Claude API key
console.anthropic.com
GATEWAY_API_KEY
Your custom gateway key
Generate a random secure string


Optional Environment Variables

Variable
Description
Default
GLM_API_KEY
Zhipu GLM-4 API key
Uses OpenAI key as fallback
GLM_API_ENDPOINT
GLM-4 API endpoint
https://open.bigmodel.cn/api/paas/v4
MISTRAL_API_URL
Mistral API endpoint
https://api.mistral.ai/v1





📊 API Endpoints Reference

1. Generate Content

Endpoint: POST /api/ai/intelligent-router?action=generate

Request:

JSON


{
  "prompt": "Your prompt here",
  "primaryModel": "mixtral-8x22b-instruct",
  "fallbackModel": "glm-4"
}


Response:

JSON


{
  "success": true,
  "content": "Generated content...",
  "modelUsed": "mixtral-8x22b-instruct",
  "timestamp": "2025-11-23T..."
}


2. Fact-Check Claim

Endpoint: POST /api/ai/intelligent-router?action=fact-check

Request:

JSON


{
  "claim": "Claim to verify",
  "searchResults": ["Optional context..."]
}


Response:

JSON


{
  "success": true,
  "finalVerdict": "Fact-Checked: True",
  "consensus": "Consensus: 2/3 judges agree",
  "judgeResults": [...],
  "evidenceBlock": "Markdown evidence..."
}


3. Generate with Fact-Check

Endpoint: POST /api/ai/intelligent-router?action=generate-with-fact-check

Request:

JSON


{
  "prompt": "Your prompt here",
  "enableFactCheck": true
}


Response:

JSON


{
  "success": true,
  "content": "Content with evidence blocks...",
  "modelUsed": "mixtral-8x22b-instruct",
  "factChecks": [...],
  "factCheckCount": 3
}





🐛 Troubleshooting

Issue: "Unauthorized" Error

Cause: Missing or incorrect GATEWAY_API_KEY

Solution:

1.
Check that GATEWAY_API_KEY is set in .env.local or Vercel environment variables

2.
Ensure the Authorization header matches: Authorization: Bearer your_gateway_key

Issue: "Primary model failed"

Cause: Invalid Mistral API key or rate limit exceeded

Solution:

1.
Verify your Mistral API key at console.mistral.ai

2.
Check your usage limits

3.
System will automatically fall back to GLM-4 if configured

Issue: "Fact-checking returns Inconclusive"

Cause: Insufficient context or ambiguous claim

Solution:

1.
Provide more specific claims

2.
Include searchResults array with relevant context

3.
Ensure all fact-checker API keys are valid

Issue: TypeScript Compilation Errors

Cause: Missing type definitions or syntax errors

Solution:

Bash


npm run typecheck


Issue: Port Already in Use

Cause: Another process is using port 3000

Solution:

Bash


# Kill the process
lsof -ti:3000 | xargs kill -9

# Or use a different port
PORT=3001 npm run dev





📚 Additional Resources

•
Full Documentation: See AI_CONNECTIONS_README.md

•
Deployment Status: See DEPLOYMENT_STATUS.md

•
Test Suite: Run node test-ai-connections.js

•
Main README: See README.md




🎯 Next Steps After Deployment

1.
Monitor Performance

•
Check Vercel analytics dashboard

•
Monitor API usage and costs

•
Review error logs



2.
Integrate with Existing Systems

•
Connect to Airtable workflows

•
Integrate with MCP servers

•
Add to existing pipelines



3.
Optimize Configuration

•
Adjust model selection based on use case

•
Fine-tune temperature and token limits

•
Implement caching for repeated queries



4.
Scale Up

•
Add more judge models for higher accuracy

•
Implement batch processing

•
Set up monitoring and alerting






💡 Pro Tips

1.
Cost Optimization: Use Groq for fast, cheap inference when possible

2.
Accuracy: Enable fact-checking for critical content

3.
Speed: Disable fact-checking for non-critical content

4.
Reliability: Always configure the GLM-4 fallback

5.
Security: Rotate your GATEWAY_API_KEY regularly




✅ Deployment Checklist




API keys configured in .env.local




Local testing completed successfully




Deployed to Vercel




Environment variables added to Vercel




Production endpoints tested




Documentation reviewed




Monitoring enabled




Team notified




🆘 Need Help?

1.
Check the logs: vercel logs or browser console

2.
Run diagnostics: ./verify-ai-deployment.sh

3.
Test locally: npm run dev and node test-ai-connections.js

4.
Review docs: AI_CONNECTIONS_README.md

5.
Check GitHub Issues: Report bugs at the repository




Deployment Time: ~10 minutes
Difficulty: Easy
Cost: Free tier available (pay-as-you-go for API calls)




🎉 Congratulations! You're ready to deploy The Lab Verse Monitoring
