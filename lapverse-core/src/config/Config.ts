import { z } from 'zod';

const envSchema = z.object({
  DASHSCOPE_API_KEY: z.string().min(1, 'Qwen API key required'),
  MOONSHOT_API_KEY: z.string().min(1, 'Kimi API key required'),
});

export class Config {
    static env: z.infer<typeof envSchema>;

  static load() {
    this.env = envSchema.parse(process.env);
  }
}