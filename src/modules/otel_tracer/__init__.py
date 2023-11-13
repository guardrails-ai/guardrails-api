import os
from opentelemetry import trace
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter


# configure
OTEL_EXPORTER_OTLP_ENDPOINT = os.environ.get('OTEL_EXPORTER_OTLP_ENDPOINT', 'http://localhost:4317') # 'http://otel-collector:4317')
OTEL_TRACE_SINK = os.environ.get('OTEL_TRACE_SINK')
endpoint = OTEL_TRACE_SINK or OTEL_EXPORTER_OTLP_ENDPOINT
print("OTEL_EXPORTER_OTLP_ENDPOINT: ", OTEL_EXPORTER_OTLP_ENDPOINT)
print("OTEL_TRACE_SINK: ", OTEL_TRACE_SINK)
print("endpoint: ", endpoint)
insecure = not endpoint.startswith('https://')
provider = trace.get_tracer_provider()
processor = BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint, insecure=insecure))
print("exporter endpoint: ", processor.span_exporter._endpoint)
provider.add_span_processor(processor)

service_name = os.environ.get('OTEL_SERVICE_NAME', 'guardrails-api')
otel_tracer = trace.get_tracer(service_name)