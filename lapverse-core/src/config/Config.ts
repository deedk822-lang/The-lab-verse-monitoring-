import { z } from 'zod';

const envSchema = z.object({
  DASHSCOPE_API_KEY: z.string().min(1, 'Qwen API key required'),
  MOONSHOT_API_KEY: z.string().min(1, 'Kimi API key required'),
  KAGGLE_API_KEY: z.string().min(1, 'Kaggle key required for evolutions'),
  DD_API_KEY: z.string().min(1, 'Datadog key required for traces'),
  DD_SITE: z.string().default('datadoghq.com'),
});

export class Config {
    static env: z.infer<typeof envSchema>;

  static load() {
    this.env = envSchema.parse(process.env);
  }
}