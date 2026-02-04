"""
OpenTelemetry Tracing Configuration for Noon-E-Commerce API
Supports OTLP export to Jaeger, Zipkin, or other compatible backends
"""

import os
import logging

logger = logging.getLogger(__name__)

# Configuration from environment
OTEL_ENABLED = os.environ.get('OTEL_ENABLED', 'false').lower() == 'true'
OTEL_SERVICE_NAME = os.environ.get('OTEL_SERVICE_NAME', 'noon-ecommerce-api')
OTEL_EXPORTER_ENDPOINT = os.environ.get('OTEL_EXPORTER_OTLP_ENDPOINT', 'http://localhost:4317')
OTEL_SAMPLE_RATE = float(os.environ.get('OTEL_SAMPLE_RATE', '0.1'))  # 10% sampling by default


def setup_tracing(app):
    """
    Configure OpenTelemetry tracing for FastAPI app.
    
    Environment variables:
    - OTEL_ENABLED: Set to 'true' to enable tracing
    - OTEL_SERVICE_NAME: Service name for traces (default: noon-ecommerce-api)
    - OTEL_EXPORTER_OTLP_ENDPOINT: OTLP collector endpoint (default: http://localhost:4317)
    - OTEL_SAMPLE_RATE: Sampling rate 0.0-1.0 (default: 0.1 = 10%)
    """
    if not OTEL_ENABLED:
        logger.info("OpenTelemetry tracing is disabled. Set OTEL_ENABLED=true to enable.")
        return
    
    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.sdk.resources import Resource, SERVICE_NAME
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.sdk.trace.sampling import TraceIdRatioBased
        
        # Create resource with service name
        resource = Resource(attributes={
            SERVICE_NAME: OTEL_SERVICE_NAME
        })
        
        # Create sampler (rate-based sampling)
        sampler = TraceIdRatioBased(OTEL_SAMPLE_RATE)
        
        # Create tracer provider
        provider = TracerProvider(resource=resource, sampler=sampler)
        
        # Configure OTLP exporter
        otlp_exporter = OTLPSpanExporter(endpoint=OTEL_EXPORTER_ENDPOINT, insecure=True)
        
        # Add batch processor for efficient export
        provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
        
        # Set as global tracer provider
        trace.set_tracer_provider(provider)
        
        # Instrument FastAPI
        FastAPIInstrumentor.instrument_app(app)
        
        logger.info(f"OpenTelemetry tracing enabled: service={OTEL_SERVICE_NAME}, endpoint={OTEL_EXPORTER_ENDPOINT}, sample_rate={OTEL_SAMPLE_RATE}")
        
    except ImportError as e:
        logger.warning(f"OpenTelemetry packages not installed, tracing disabled: {e}")
    except Exception as e:
        logger.error(f"Failed to configure OpenTelemetry tracing: {e}")


def get_tracer(name: str = __name__):
    """Get a tracer instance for manual instrumentation."""
    if not OTEL_ENABLED:
        return None
    
    try:
        from opentelemetry import trace
        return trace.get_tracer(name)
    except ImportError:
        return None
