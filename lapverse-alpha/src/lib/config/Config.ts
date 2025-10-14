import { z } from 'zod';

const ConfigSchema = z.object({
  PORT: z.coerce.number().default(3000),
  LOG_LEVEL: z.string().default('INFO'),
  LOCALAI_BASE_URL: z.string().default('http://localhost:8000'),
  ARGILLA_BASE_URL: z.string().default('http://localhost:6900'),
  ARGILLA_API_KEY: z.string().default('lapverse-internal'),
  ARGILLA_WORKSPACE: z.string().default('lapverse'),
  BLOCKCHAIN_RPC_URL: z.string().default('https://mainnet.base.org'),
  BLOCKCHAIN_PRIVATE_KEY: z.string().optional(),
  ALPHA_TOKEN_ADDRESS: z.string().optional(),
  ESCROW_CONTRACT_ADDRESS: z.string().optional(),
  BASE_URL: z.string().url().default('http://localhost:3000'),
});

export class ConfigManager {
  private config: z.infer<typeof ConfigSchema>;

  constructor() {
    this.config = ConfigSchema.parse(process.env);
  }

  get() {
    return this.config;
  }
}

export const config = new ConfigManager();