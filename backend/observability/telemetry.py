from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
)
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor


def setup_telemetry(app):
    # Create tracer provider
    provider = TracerProvider(
        resource=Resource.create(
            {
                "service.name": "aiko-bank",
                "service.version": "1.0.0",
            }
        )
    )

    # Install provider once
    current = trace.get_tracer_provider()

    if current.__class__.__name__ != "TracerProvider":
        trace.set_tracer_provider(provider)
    else:
        provider = current

    # Console exporter (great for debugging)
    provider.add_span_processor(
        BatchSpanProcessor(
            ConsoleSpanExporter()
        )
    )

    # OTLP exporter (Collector)
    provider.add_span_processor(
        BatchSpanProcessor(
            OTLPSpanExporter(
                endpoint="http://localhost:4317",
                insecure=True,
            )
        )
    )

    # Auto instrument FastAPI
    FastAPIInstrumentor.instrument_app(app)

    return trace.get_tracer("aiko-bank")