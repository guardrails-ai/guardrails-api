# !!! UPDATE ME !!!
# See Tracer setup
import os
from opentelemetry import metrics

service_name = os.environ.get("OTEL_SERVICE_NAME", "guardrails-api")
provider = metrics.get_meter_provider()
otel_meter = provider.get_meter(service_name)
