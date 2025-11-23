/**
 * API Endpoint: Intelligent Router
 * Handles AI generation requests with fact-checking and fallback mechanisms
 */

import type { NextApiRequest, NextApiResponse } from 'next';
import {
  generateContentWithFallback,
  generateFactCheckedContent,
  factCheckClaim
} from '../../../src/ai-connections/intelligent-router';

interface GenerateRequest {
  prompt: string;
  enableFactCheck?: boolean;
  primaryModel?: string;
  fallbackModel?: string;
}

interface FactCheckRequest {
  claim: string;
  searchResults?: string[];
}

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  // CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  // Authentication check
  const authHeader = req.headers.authorization;
  const apiKey = process.env.GATEWAY_API_KEY;

  if (apiKey && authHeader !== `Bearer ${apiKey}`) {
    return res.status(401).json({
      error: 'Unauthorized',
      message: 'Invalid or missing API key'
    });
  }

  if (req.method !== 'POST') {
    return res.status(405).json({
      error: 'Method Not Allowed',
      message: 'Only POST requests are supported'
    });
  }

  const { action } = req.query;

  try {
    switch (action) {
      case 'generate':
        return await handleGenerate(req, res);

      case 'generate-with-fact-check':
        return await handleGenerateWithFactCheck(req, res);

      case 'fact-check':
        return await handleFactCheck(req, res);

      default:
        return res.status(400).json({
          error: 'Bad Request',
          message: 'Invalid action. Supported actions: generate, generate-with-fact-check, fact-check'
        });
    }
  } catch (error) {
    console.error('Intelligent Router error:', error);
    return res.status(500).json({
      error: 'Internal Server Error',
      message: error instanceof Error ? error.message : 'Unknown error occurred'
    });
  }
}

/**
 * Handle simple content generation with fallback
 */
async function handleGenerate(req: NextApiRequest, res: NextApiResponse) {
  const { prompt, primaryModel, fallbackModel } = req.body as GenerateRequest;

  if (!prompt) {
    return res.status(400).json({
      error: 'Bad Request',
      message: 'Prompt is required'
    });
  }

  const result = await generateContentWithFallback(
    prompt,
    primaryModel,
    fallbackModel
  );

  return res.status(200).json({
    success: result.success,
    content: result.content,
    modelUsed: result.modelUsed,
    timestamp: new Date().toISOString()
  });
}

/**
 * Handle content generation with automatic fact-checking
 */
async function handleGenerateWithFactCheck(req: NextApiRequest, res: NextApiResponse) {
  const { prompt, enableFactCheck = true } = req.body as GenerateRequest;

  if (!prompt) {
    return res.status(400).json({
      error: 'Bad Request',
      message: 'Prompt is required'
    });
  }

  const result = await generateFactCheckedContent(prompt, enableFactCheck);

  return res.status(200).json({
    success: result.success,
    content: result.content,
    modelUsed: result.modelUsed,
    factChecks: result.factChecks,
    factCheckCount: result.factChecks?.length || 0,
    timestamp: new Date().toISOString()
  });
}

/**
 * Handle standalone fact-checking
 */
async function handleFactCheck(req: NextApiRequest, res: NextApiResponse) {
  const { claim, searchResults } = req.body as FactCheckRequest;

  if (!claim) {
    return res.status(400).json({
      error: 'Bad Request',
      message: 'Claim is required'
    });
  }

  const result = await factCheckClaim(claim, searchResults);

  return res.status(200).json({
    success: true,
    claim: result.claim,
    finalVerdict: result.finalVerdict,
    consensus: result.consensus,
    judgeResults: result.judgeResults,
    evidenceBlock: result.evidenceBlock,
    timestamp: new Date().toISOString()
  });
}
