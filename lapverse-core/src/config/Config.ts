import { z } from 'zod';

const envSchema = z.object({
  DASHSCOPE_API_KEY: z.string().min(1, 'Qwen API key required'),
  MOONSHOT_API_KEY: z.string().min(1, 'Kimi API key required'),
  KAGGLE_API_KEY: z.string().min(1, 'Kaggle key required for evolutions'),
  DD_API_KEY: z.string().min(1, 'Datadog key required for traces'),
  DD_SITE: z.string().default('datadoghq.com'),

  // OTel Exporter Configuration
  OTEL_EXPORTER_OTLP_ENDPOINT: z.string().default('http://localhost:4318'),
  OTEL_EXPORTER_OTLP_HEADERS: z.string().optional(),
  OTEL_EXPORTER_OTLP_TIMEOUT: z.string().default('10000'),
  OTEL_EXPORTER_OTLP_PROTOCOL: z.string().default('http/protobuf'),

  // OTel Resource Configuration
  OTEL_SERVICE_NAME: z.string().default('lapverse-core'),
  OTEL_RESOURCE_ATTRIBUTES: z.string().optional(),

  // OTel Sampling Configuration
  OTEL_TRACES_SAMPLER: z.string().default('parentbased_always_on'),
  OTEL_TRACES_SAMPLER_ARG: z.string().default('1.0'),
});

export class Config {
    static env: z.infer<typeof envSchema>;

  static load() {
    this.env = envSchema.parse(process.env);
  }
}