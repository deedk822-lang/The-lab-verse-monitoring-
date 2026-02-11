import { z } from 'zod';

const ConfigSchema = z.object({
  VITE_PORT: z.coerce.number().default(3000),
  GEMINI_API_KEY: z.string().optional(),
  TONGYI_API_KEY: z.string().optional(),
  PERPLEXITY_API_KEY: z.string().optional(),
  AYSHARE_API_KEY: z.string().optional(),
});

// This is a placeholder for a real config loader.
// In a real app, this would come from environment variables.
export const Config = ConfigSchema.parse({
    VITE_PORT: 3000,
});