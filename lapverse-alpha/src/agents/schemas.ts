import { z } from 'zod';

export const QwenResponseSchema = z.object({
  reasoning: z.array(z.string()),
  solution: z.string(),
  originalityScore: z.number().min(0).max(1)
});
export type QwenResponse = z.infer<typeof QwenResponseSchema>;

export const GrokPlanSchema = z.object({
  plan: z.array(z.string()).optional(),
  delegated: z.array(z.any()).optional()
});
export type GrokPlan = z.infer<typeof GrokPlanSchema>;