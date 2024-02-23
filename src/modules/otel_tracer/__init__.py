import os
from opentelemetry import trace
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
    OTLPSpanExporter as GrpcExporter,
)

# configure
OTEL_EXPORTER_OTLP_ENDPOINT = os.environ.get(
    "OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317"
)  # 'http://otel-collector:4317')
OTEL_TRACE_SINK = os.environ.get("OTEL_TRACE_SINK")
endpoint = OTEL_TRACE_SINK or OTEL_EXPORTER_OTLP_ENDPOINT
print("OTEL_EXPORTER_OTLP_ENDPOINT: ", OTEL_EXPORTER_OTLP_ENDPOINT)
print("OTEL_TRACE_SINK: ", OTEL_TRACE_SINK)
print("endpoint: ", endpoint)
insecure = not endpoint.startswith("https://")
provider = trace.get_tracer_provider()

span_processors = provider._active_span_processor._span_processors
span_processor = span_processors[0] if len(span_processors) > 0 else None
span_exporter = (
    span_processor.span_exporter
    if span_processor is not None
    else GrpcExporter()
)

simple_processor = SimpleSpanProcessor(span_exporter)
is_lambda = os.environ.get("AWS_EXECUTION_ENV", "").startswith("AWS_Lambda_")
is_fargate = os.environ.get("AWS_EXECUTION_ENV", "").startswith("AWS_ECS_")
if is_lambda or is_fargate or not span_processor:
    provider._active_span_processor._span_processors = (simple_processor,)

service_name = os.environ.get("OTEL_SERVICE_NAME", "guardrails-api")
otel_tracer = trace.get_tracer(service_name)
