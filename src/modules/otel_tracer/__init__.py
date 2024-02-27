import os
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    SimpleSpanProcessor
)
from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
    OTLPSpanExporter,
)
# from rich import print


# configure
service_name = os.environ.get("OTEL_SERVICE_NAME", "guardrails-api")
OTEL_EXPORTER_OTLP_ENDPOINT = os.environ.get(
    "OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317"
)  # 'http://otel-collector:4317')
OTEL_TRACE_SINK = os.environ.get(
    "OTEL_EXPORTER_OTLP_TRACES_ENDPOINT",
    f"{OTEL_EXPORTER_OTLP_ENDPOINT}/v1/traces"
)
endpoint = OTEL_TRACE_SINK
insecure = not endpoint.startswith("https://")

resource = Resource(attributes={
    SERVICE_NAME: service_name
  })

provider = TracerProvider(resource=resource)

span_exporter = OTLPSpanExporter(endpoint=endpoint)

processor = BatchSpanProcessor(span_exporter)
# processor = SimpleSpanProcessor(span_exporter)

is_lambda = os.environ.get("AWS_EXECUTION_ENV", "").startswith("AWS_Lambda_")
if is_lambda:
    processor = SimpleSpanProcessor(span_exporter)

provider.add_span_processor(processor)

# Creates a tracer from the global tracer provider
otel_tracer = provider.get_tracer(service_name)
