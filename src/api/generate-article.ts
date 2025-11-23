// File: src/api/generate-article.ts
// This is the Vercel App's "Intelligent Router" function with the GLM-4 Fallback.

import { VercelRequest, VercelResponse } from '@vercel/node';

// Assume these are set as environment variables in Vercel
const CDATA_API_ENDPOINT = process.env.CDATA_CONNECT_API;
const CDATA_API_KEY = process.env.CDATA_API_KEY;
const GLM4_API_ENDPOINT = 'https://api.glm-4.com/v1/chat/completions'; // Placeholder URL
const GLM4_API_KEY = process.env.GLM4_API_KEY;

// Helper function to call the primary model via CData Connect
async function callPrimaryModel(prompt: string, primaryModel: string) {
    if (!CDATA_API_ENDPOINT || !CDATA_API_KEY) {
        throw new Error("CData API configuration missing.");
    }

    const query = `SELECT content FROM ${primaryModel} WHERE prompt = '${prompt.replace(/'/g, "''")}'`;
    
    const response = await fetch(CDATA_API_ENDPOINT, {
        method: 'POST',
        headers: { 
            'Authorization': `Bearer ${CDATA_API_KEY}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ query })
    });

    if (!response.ok) {
        // Throwing an error here triggers the fallback in the catch block
        const errorText = await response.text();
        throw new Error(`Primary model (${primaryModel}) failed via CData: ${errorText}`);
    }
    
    const result = await response.json();
    // Assuming CData returns a structured result with data array
    if (result.data && result.data.length > 0) {
        return { content: result.data[0].content, source: primaryModel };
    }
    
    throw new Error(`Primary model (${primaryModel}) returned empty content.`);
}

// Helper function for the GLM-4 direct fallback
async function callGLM4Fallback(prompt: string) {
    if (!GLM4_API_KEY) {
        throw new Error("GLM-4 Fallback API key missing.");
    }

    console.warn(`Primary model failed. Initiating fallback to GLM-4.`);
    
    // Direct GLM-4 API call (using a standard OpenAI-like payload structure)
    const glm4Response = await fetch(GLM4_API_ENDPOINT, {
        method: 'POST',
        headers: { 
            'Authorization': `Bearer ${GLM4_API_KEY}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ 
            model: 'glm-4',
            messages: [{ role: 'user', content: prompt }]
        })
    });

    if (!glm4Response.ok) {
        const errorText = await glm4Response.text();
        throw new Error(`FATAL: Primary and Fallback (GLM-4) models both failed. Error: ${errorText}`);
    }

    const glm4Result = await glm4Response.json();
    // Assuming the response structure is standard chat completion
    const content = glm4Result.choices[0].message.content;
    
    return { content: content, source: 'GLM-4 (Fallback)' };
}


export default async function generateArticle(req: VercelRequest, res: VercelResponse) {
    if (req.method !== 'POST') {
        return res.status(405).send('Method Not Allowed');
    }

    const { prompt, primaryModel = 'mistral' } = req.body;

    if (!prompt) {
        return res.status(400).json({ error: 'Missing required field: prompt' });
    }

    try {
        // 1. PRIMARY ATTEMPT: Use CData Connect to call the preferred model
        const result = await callPrimaryModel(prompt, primaryModel);
        
        // 2. SUCCESS: Return the result
        return res.status(200).json(result);

    } catch (error) {
        console.error("Primary attempt failed:", error);
        
        try {
            // 3. FALLBACK: If the primary attempt fails, call GLM-4 directly.
            const fallbackResult = await callGLM4Fallback(prompt);
            
            // 4. FALLBACK SUCCESS: Return the fallback result
            return res.status(200).json(fallbackResult);

        } catch (fallbackError) {
            // 5. FATAL FAILURE: If even the fallback fails
            console.error("Fatal error: Fallback also failed.", fallbackError);
            return res.status(500).json({ 
                error: 'Content generation failed after primary and fallback attempts.',
                details: fallbackError.message
            });
        }
    }
}
