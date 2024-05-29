import os
from opentelemetry import trace
from opentelemetry.trace import Tracer


none = "none"

def traces_are_enabled() -> bool:
    otel_traces_exporter = os.environ.get("OTEL_TRACES_EXPORTER", none)
    return otel_traces_exporter != none

def metrics_are_enabled() -> bool:
    otel_metrics_exporter = os.environ.get("OTEL_METRICS_EXPORTER", none)
    return otel_metrics_exporter != none

def logs_are_enabled() -> bool:
    otel_logs_exporter = os.environ.get("OTEL_LOGS_EXPORTER", none)
    return otel_logs_exporter != none

def otel_is_enabled() -> bool:
    return (
        traces_are_enabled()
        or metrics_are_enabled()
        or logs_are_enabled()
    )
    
def get_tracer() -> Tracer:
    service_name = os.environ.get("OTEL_SERVICE_NAME", "guardrails-api")
    tracer = trace.get_tracer(service_name)
    
    return tracer

def initialize():
    get_tracer()