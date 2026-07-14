from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
)
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor


def setup_telemetry(app):

    provider = TracerProvider()

    trace.set_tracer_provider(provider)

    provider.add_span_processor(
        BatchSpanProcessor(
            ConsoleSpanExporter()
        )
    )

    FastAPIInstrumentor.instrument_app(app)

    return trace.get_tracer("aiko-bank")