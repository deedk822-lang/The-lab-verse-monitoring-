"""
OpenTelemetry Tracing
"""

from __future__ import annotations

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from pr_fix_agent.core.config import Settings


def initialize_tracing(settings: Settings) -> None:
    """
    Initialize OpenTelemetry tracing.
    """
    if not settings.otel_enabled or not settings.otel_exporter_otlp_endpoint:
        return

    resource = Resource.create({
        "service.name": settings.otel_service_name,
        "service.version": settings.version,
        "deployment.environment": settings.environment,
    })

    provider = TracerProvider(resource=resource)

    otlp_exporter = OTLPSpanExporter(
        endpoint=settings.otel_exporter_otlp_endpoint,
        insecure=True,
    )

    processor = BatchSpanProcessor(otlp_exporter)
    provider.add_span_processor(processor)

    trace.set_tracer_provider(provider)
