import os
from src.otel.logs import logs_are_enabled
from src.otel.metrics import (
    initialize_metrics_collector,
    metrics_are_enabled,
    get_meter,  # noqa
)
from src.otel.traces import (
    traces_are_enabled,
    initialize_tracer,
    get_tracer,  # noqa
)


def otel_is_enabled() -> bool:
    sdk_is_disabled = os.environ.get("OTEL_SDK_DISABLED") == "true"

    any_signals_enabled = (
        traces_are_enabled() or metrics_are_enabled() or logs_are_enabled()
    )
    return False if sdk_is_disabled else any_signals_enabled


def initialize():
    initialize_tracer()
    initialize_metrics_collector()
    # Logs are supported yet in the Python SDK
    # initialize_logs_collector()
