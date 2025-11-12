import { NodeSDK } from '@opentelemetry/sdk-node';
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-http';
import { OTLPMetricExporter } from '@opentelemetry/exporter-metrics-otlp-http';
import { PeriodicExportingMetricReader } from '@opentelemetry/sdk-metrics';
import { Resource } from '@opentelemetry/resources';
import { SemanticResourceAttributes } from '@opentelemetry/semantic-conventions';
import { HttpInstrumentation } from '@opentelemetry/instrumentation-http';
import { ExpressInstrumentation } from '@opentelemetry/instrumentation-express';

// Only initialize if OTLP endpoint is configured
if (!process.env.OTEL_EXPORTER_OTLP_ENDPOINT) {
  console.log('⚠️  OpenTelemetry not configured - skipping initialization');
  // Do not exit, just skip initialization
} else {
    // Parse authorization header
    const authHeader = process.env.OTEL_EXPORTER_OTLP_HEADERS?.replace('Authorization=', '') || '';

    // Create resource with service information
    const resource = new Resource({
      [SemanticResourceAttributes.SERVICE_NAME]: process.env.OTEL_SERVICE_NAME || 'ai-provider-monitoring',
      [SemanticResourceAttributes.SERVICE_VERSION]: process.env.npm_package_version || '1.0.0',
      [SemanticResourceAttributes.DEPLOYMENT_ENVIRONMENT]: process.env.NODE_ENV || 'production',
    });

    // Configure trace exporter
    const traceExporter = new OTLPTraceExporter({
      url: `${process.env.OTEL_EXPORTER_OTLP_ENDPOINT}/v1/traces`,
      headers: {
        Authorization: authHeader,
      },
      timeoutMillis: 5000,
    });

    // Configure metric exporter
    const metricExporter = new OTLPMetricExporter({
      url: `${process.env.OTEL_EXPORTER_OTLP_ENDPOINT}/v1/metrics`,
      headers: {
        Authorization: authHeader,
      },
      timeoutMillis: 5000,
    });

    // Create metric reader with 10-second export interval
    const metricReader = new PeriodicExportingMetricReader({
      exporter: metricExporter,
      exportIntervalMillis: 10000, // Export every 10 seconds
    });

    // Initialize OpenTelemetry SDK
    const sdk = new NodeSDK({
      resource,
      traceExporter,
      metricReader,
      instrumentations: [
        new HttpInstrumentation({
          ignoreIncomingPaths: ['/health', '/favicon.ico'],
        }),
        new ExpressInstrumentation(),
      ],
    });

    // Start the SDK
    sdk.start();

    console.log('✅ OpenTelemetry initialized');
    console.log(`   Service: ${resource.attributes[SemanticResourceAttributes.SERVICE_NAME]}`);
    console.log(`   Environment: ${resource.attributes[SemanticResourceAttributes.DEPLOYMENT_ENVIRONMENT]}`);
    console.log(`   Endpoint: ${process.env.OTEL_EXPORTER_OTLP_ENDPOINT}`);

    // Graceful shutdown
    process.on('SIGTERM', () => {
      sdk.shutdown()
        .then(() => console.log('✅ OpenTelemetry shut down successfully'))
        .catch((error) => console.error('❌ Error shutting down OpenTelemetry:', error))
        .finally(() => process.exit(0));
    });

    // Handle uncaught errors
    process.on('unhandledRejection', (error) => {
      console.error('❌ Unhandled rejection:', error);
    });

    // export default sdk; // Not exporting as it's not needed elsewhere
}
