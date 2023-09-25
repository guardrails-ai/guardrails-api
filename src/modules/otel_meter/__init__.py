from opentelemetry import metrics


provider = metrics.get_meter_provider()
otel_meter = provider.get_meter(__name__)