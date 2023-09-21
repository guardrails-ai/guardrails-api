import os
# import math
from opentelemetry import metrics
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import (
    OTLPMetricExporter,
)
# import opentelemetry.metrics as metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader

from src.modules.resource import resource

OTLP_ENDPOINT = os.environ.get('OTLP_ENDPOINT', 'http://otel-collector:4317')
print("\n")
print("============ otel_meter env vars: ============")
print("os.environ.get('OTLP_ENDPOINT'): ", os.environ.get('OTLP_ENDPOINT'))
print("OTLP_ENDPOINT:", OTLP_ENDPOINT)
print("\n")

reader = PeriodicExportingMetricReader(
    OTLPMetricExporter(endpoint=OTLP_ENDPOINT)
)
provider = MeterProvider(resource=resource, metric_readers=[reader])
metrics.set_meter_provider(provider)
# __exporter = OTLPMetricExporter(endpoint=OTLP_ENDPOINT, insecure=True)
# metric_reader = PeriodicExportingMetricReader(__exporter, export_interval_millis=math.inf)
# __provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
# set_meter_provider(__provider)

otel_meter = metrics.get_meter_provider().get_meter(__name__)