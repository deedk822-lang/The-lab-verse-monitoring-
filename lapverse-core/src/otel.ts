import { NodeSDK } from '@opentelemetry/sdk-node';
import { getNodeAutoInstrumentations } from '@opentelemetry/auto-instrumentations-node';
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-http';
import { OTLPMetricExporter } from '@opentelemetry/exporter-metrics-otlp-http';
import { OTLPLogExporter } from '@opentelemetry/exporter-logs-otlp-http';
import { PeriodicExportingMetricReader } from '@opentelemetry/sdk-metrics';
import { BatchLogRecordProcessor } from '@opentelemetry/sdk-logs';
import { Resource } from '@opentelemetry/resources';
import { SemanticResourceAttributes } from '@opentelemetry/semantic-conventions';
import { Config } from './config/Config';

Config.load();  // Validates DD_API_KEY

const sdk = new NodeSDK({
  resource: new Resource({
    [SemanticResourceAttributes.SERVICE_NAME]: 'lapverse-monitoring',
    [SemanticResourceAttributes.SERVICE_VERSION]: '2.1',
    [SemanticResourceAttributes.DEPLOYMENT_ENVIRONMENT]: 'prod'
  }),
  traceExporter: new OTLPTraceExporter({
    url: `https://api.${Config.env.DD_SITE}/v1/traces`,
    headers: { 'DD-API-KEY': Config.env.DD_API_KEY },
    timeoutMillis: 5000
  }),
  metricReader: new PeriodicExportingMetricReader({
    exporter: new OTLPMetricExporter({
      url: `https://api.${Config.env.DD_SITE}/v1/metrics`,
      headers: { 'DD-API-KEY': Config.env.DD_API_KEY },
      timeoutMillis: 5000
    })
  }),
  logRecordProcessor: new BatchLogRecordProcessor(
    new OTLPLogExporter({
      url: `https://http-intake.logs.${Config.env.DD_SITE}/v1/input`,
      headers: { 'DD-API-KEY': Config.env.DD_API_KEY },
      timeoutMillis: 5000
    })
  ),
  instrumentations: [getNodeAutoInstrumentations()]
});

sdk.start();

process.on('SIGTERM', () => sdk.shutdown().catch(console.error));