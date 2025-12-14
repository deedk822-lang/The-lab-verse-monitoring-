// File: src/api/generate-article.ts
// Simplified article generation using GLM-4 API directly

import { VercelRequest, VercelResponse } from '@vercel/node';

const GLM4_API_ENDPOINT = 'https://open.bigmodel.cn/api/paas/v4/chat/completions';
const GLM4_API_KEY = process.env.GLM4_API_KEY;

// Helper function to call GLM-4 API
async function callGLM4(prompt: string, model: string = 'glm-4-plus') {
    if (!GLM4_API_KEY) {
        throw new Error("GLM-4 API key missing. Please set GLM4_API_KEY environment variable.");
    }

    console.log(`Calling GLM-4 model: ${model}`);
    
    const response = await fetch(GLM4_API_ENDPOINT, {
        method: 'POST',
        headers: { 
            'Authorization': `Bearer ${GLM4_API_KEY}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ 
            model: model,
            messages: [
                { 
                    role: 'user', 
                    content: prompt 
                }
            ],
            temperature: 0.7,
            top_p: 0.9,
            max_tokens: 2000
        })
    });

    if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`GLM-4 API call failed (${response.status}): ${errorText}`);
    }

    const result = await response.json();
    
    // Extract content from response
    if (result.choices && result.choices.length > 0) {
        const content = result.choices[0].message.content;
        return { 
            content: content, 
            source: model,
            usage: result.usage || null
        };
    }
    
    throw new Error('GLM-4 returned empty content.');
}

export default async function generateArticle(req: VercelRequest, res: VercelResponse) {
    if (req.method !== 'POST') {
        return res.status(405).json({ error: 'Method Not Allowed' });
    }

    const { prompt, model = 'glm-4-plus' } = req.body;

    if (!prompt) {
        return res.status(400).json({ error: 'Missing required field: prompt' });
    }

    try {
        // Call GLM-4 API
        const result = await callGLM4(prompt, model);
        
        // Return successful result
        return res.status(200).json({
            success: true,
            ...result,
            timestamp: new Date().toISOString()
        });

    } catch (error: any) {
        console.error("Content generation failed:", error);
        
        return res.status(500).json({ 
            success: false,
            error: 'Content generation failed',
            details: error.message,
            timestamp: new Date().toISOString()
        });
    }
}
