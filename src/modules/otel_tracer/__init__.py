from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

from src.modules.resource import resource

# configure
trace.set_tracer_provider(TracerProvider(resource=resource))
__otlp_span_exporter = OTLPSpanExporter(endpoint='otel-collector:4317', insecure=True)
__span_processor = SimpleSpanProcessor(__otlp_span_exporter)
trace.get_tracer_provider().add_span_processor(__span_processor)

otel_tracer = trace.get_tracer(__name__)