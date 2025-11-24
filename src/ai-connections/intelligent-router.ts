// src/ai-connections/intelligent-router.ts
import { modelConfig, providerEndpoints } from './mistral-config';
import { streamText } from 'ai';

// A helper function to call the AI providers
async function callAI(provider: keyof typeof providerEndpoints, model: string, prompt: string) {
    const endpoint = providerEndpoints[provider];
    const apiKey = process.env[`${provider.toUpperCase()}_API_KEY`];

    if (!apiKey) {
        throw new Error(`API key for ${provider} is not set.`);
    }

    const result = await streamText({
        model,
        prompt,
    });


    return result.text;
}

// Main function to generate content with fallback
export async function generateContent(prompt: string, primaryModel: string = modelConfig.visionary) {
    try {
        // @ts-ignore
        return await callAI('mistral', primaryModel, prompt);
    } catch (error) {
        console.warn(`Primary model ${primaryModel} failed. Falling back to GLM-4.`, error);
        // @ts-ignore
        return await callAI('glm', modelConfig.fallback, prompt);
    }
}

// Function to perform fact-checking
export async function factCheckClaims(claims: string[]) {
    const factCheckingPromises = claims.map(async (claim) => {
        const judges = [
            // @ts-ignore
            callAI('google', modelConfig.factChecker1, `Fact-check the following claim and respond with only "True", "False", or "Inconclusive": "${claim}"`),
            // @ts-ignore
            callAI('groq', modelConfig.factChecker2, `Fact-check the following claim and respond with only "True", "False", or "Inconclusive": "${claim}"`),
            // @ts-ignore
            callAI('anthropic', modelConfig.factChecker3, `Fact-check the following claim and respond with only "True", "False", or "Inconclusive": "${claim}"`),
        ];

        const verdicts = await Promise.all(judges);
        const trueCount = verdicts.filter((v) => v.toLowerCase().includes('true')).length;

        let finalVerdict = 'Inconclusive';
        if (trueCount >= 2) {
            finalVerdict = 'True';
        } else if (verdicts.length - trueCount >= 2) {
            finalVerdict = 'False';
        }

        return {
            claim,
            finalVerdict,
            verdicts: {
                gemini: verdicts[0],
                groq: verdicts[1],
                anthropic: verdicts[2],
            },
        };
    });

    return Promise.all(factCheckingPromises);
}

// AI-Powered Tax Agent Assistant
export async function getTaxAdvice(businessPlan: string) {
    const prompt = `You are a Certified Public Accountant (CPA) Agent. Analyze the following revenue strategy and provide a 5-point summary of potential tax liabilities and 3 actionable tax optimization suggestions.

Business Plan:
${businessPlan}`;

    // @ts-ignore
    return callAI('mistral', modelConfig.auditor, prompt);
}
