import { NodeSDK } from '@opentelemetry/sdk-node';
import { getNodeAutoInstrumentations } from '@opentelemetry/auto-instrumentations-node';
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-http';
import { OTLPMetricExporter } from '@opentelemetry/exporter-metrics-otlp-http';
import { OTLPLogExporter } from '@opentelemetry/exporter-logs-otlp-http';
import { PeriodicExportingMetricReader } from '@opentelemetry/sdk-metrics';
import { BatchLogRecordProcessor } from '@opentelemetry/sdk-logs';
import { Resource } from '@opentelemetry/resources';
import { SemanticResourceAttributes } from '@opentelemetry/semantic-conventions';
import { TraceIdRatioBasedSampler } from '@opentelemetry/sdk-trace-node';
import { Config } from './config/Config';

Config.load();

const parseHeaders = (headers: string | undefined): Record<string, string> => {
  if (!headers) return {};
  return Object.fromEntries(
    headers.split(',').map(pair => {
      const [key, ...valueParts] = pair.split('=');
      return [key, valueParts.join('=')];
    })
  );
};

const resourceAttributes = {
  [SemanticResourceAttributes.SERVICE_NAME]: Config.env.OTEL_SERVICE_NAME,
  ...parseHeaders(Config.env.OTEL_RESOURCE_ATTRIBUTES),
};

const traceExporter = new OTLPTraceExporter({
  url: `${Config.env.OTEL_EXPORTER_OTLP_ENDPOINT}/v1/traces`,
  headers: parseHeaders(Config.env.OTEL_EXPORTER_OTLP_HEADERS),
  timeoutMillis: parseInt(Config.env.OTEL_EXPORTER_OTLP_TIMEOUT, 10),
});

const metricExporter = new OTLPMetricExporter({
    url: `${Config.env.OTEL_EXPORTER_OTLP_ENDPOINT}/v1/metrics`,
    headers: parseHeaders(Config.env.OTEL_EXPORTER_OTLP_HEADERS),
    timeoutMillis: parseInt(Config.env.OTEL_EXPORTER_OTLP_TIMEOUT, 10),
});

const logExporter = new OTLPLogExporter({
    url: `${Config.env.OTEL_EXPORTER_OTLP_ENDPOINT}/v1/logs`,
    headers: parseHeaders(Config.env.OTEL_EXPORTER_OTLP_HEADERS),
    timeoutMillis: parseInt(Config.env.OTEL_EXPORTER_OTLP_TIMEOUT, 10),
});

const sdk = new NodeSDK({
  resource: new Resource(resourceAttributes),
  traceExporter,
  metricReader: new PeriodicExportingMetricReader({ exporter: metricExporter }),
  logRecordProcessor: new BatchLogRecordProcessor(logExporter),
  instrumentations: [getNodeAutoInstrumentations()],
  sampler: new TraceIdRatioBasedSampler(parseFloat(Config.env.OTEL_TRACES_SAMPLER_ARG)),
});

sdk.start();

process.on('SIGTERM', () => sdk.shutdown().catch(console.error));