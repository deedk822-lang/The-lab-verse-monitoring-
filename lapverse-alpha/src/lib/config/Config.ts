import { z } from 'zod';

const envSchema = z.object({
  LOCALAI_BASE_URL: z.string().url(),
  LOCALAI_API_KEY: z.string().optional(),
  LOCALAI_QUOTA_USD: z.coerce.number().positive().default(20),
  ARGILLA_BASE_URL: z.string().url(),
  ARGILLA_API_KEY: z.string(),
  ARGILLA_WORKSPACE: z.string().default('lapverse'),
  ARGILLA_QUOTA_ROWS: z.coerce.number().positive().default(10000),
  BASE_URL: z.string().url().default('http://localhost:3000'),
});

class Config {
  private static instance: Config;
  private env: z.infer<typeof envSchema>;

  private constructor() {
    this.env = envSchema.parse(process.env);
  }

  public static getInstance(): Config {
    if (!Config.instance) {
      Config.instance = new Config();
    }
    return Config.instance;
  }

  public get() {
    return this.env;
  }
}

export const config = Config.getInstance();