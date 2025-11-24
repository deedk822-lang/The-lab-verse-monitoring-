// pages/api/ai/intelligent-router.ts
import { NextApiRequest, NextApiResponse } from 'next';
import { generateContent, factCheckClaims, getTaxAdvice } from '../../../src/ai-connections/intelligent-router';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
    const { action, prompt, claims, businessPlan, primaryModel } = req.query;

    try {
        switch (action) {
            case 'generate':
                if (typeof prompt !== 'string') {
                    return res.status(400).json({ error: 'Prompt is required' });
                }
                const content = await generateContent(prompt, primaryModel as string);
                return res.status(200).json({ content });

            case 'fact-check':
                if (!Array.isArray(claims)) {
                    return res.status(400).json({ error: 'Claims must be an array' });
                }
                const factCheckResults = await factCheckClaims(claims as string[]);
                return res.status(200).json({ factCheckResults });

            case 'tax-advice':
                if (typeof businessPlan !== 'string') {
                    return res.status(400).json({ error: 'Business plan is required' });
                }
                const taxAdvice = await getTaxAdvice(businessPlan);
                return res.status(200).json({ taxAdvice });

            default:
                return res.status(400).json({ error: 'Invalid action' });
        }
    } catch (error) {
        // @ts-ignore
        return res.status(500).json({ error: error.message });
    }
}
