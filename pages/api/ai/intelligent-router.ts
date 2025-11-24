// pages/api/ai/intelligent-router.ts
import type { NextApiRequest, NextApiResponse } from 'next';
import { generateContent, factCheckClaim } from '../../../src/ai-connections/intelligent-router';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  const { action } = req.query;
  const apiKey = req.headers.authorization?.split(' ')[1];

  if (apiKey !== process.env.GATEWAY_API_KEY) {
    return res.status(401).json({ success: false, message: 'Unauthorized' });
  }

  switch (action) {
    case 'generate':
      try {
        const { prompt, primaryModel, fallbackModel } = req.body;
        const result = await generateContent(prompt, primaryModel, fallbackModel);
        res.status(result.success ? 200 : 500).json({ ...result, timestamp: new Date().toISOString() });
      } catch (error) {
        res.status(500).json({ success: false, message: (error as Error).message });
      }
      break;

    case 'fact-check':
      try {
        const { claim, searchResults } = req.body;
        const result = await factCheckClaim(claim, searchResults || []);
        res.status(200).json({ success: true, ...result, timestamp: new Date().toISOString() });
      } catch (error) {
        res.status(500).json({ success: false, message: (error as Error).message });
      }
      break;

    case 'generate-with-fact-check':
        try {
            const { prompt } = req.body;
            const generationResult = await generateContent(prompt, 'mistral-8x22b-instruct', 'glm-4');

            if (!generationResult.success || !generationResult.content) {
                return res.status(500).json({ ...generationResult, timestamp: new Date().toISOString() });
            }

            const claims = (generationResult.content.match(/.*?(?=\.|$)/g) || []).filter(claim => claim.trim().length > 10);
            const factCheckResults = await Promise.all(claims.map(claim => factCheckClaim(claim, [])));

            const verifiedContent = factCheckResults.reduce((content, result) => {
                return content.replace(result.claim, `${result.claim}\n${result.evidenceBlock}\n`);
            }, generationResult.content);

            res.status(200).json({
                success: true,
                content: verifiedContent,
                modelUsed: generationResult.modelUsed,
                factChecks: factCheckResults,
                factCheckCount: factCheckResults.length,
                timestamp: new Date().toISOString(),
            });
        } catch (error) {
            res.status(500).json({ success: false, message: (error as Error).message });
        }
        break;

    default:
      res.status(400).json({ success: false, message: 'Invalid action specified' });
      break;
  }
}
