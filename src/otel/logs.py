import os
from src.otel.constants import none


def logs_are_enabled() -> bool:
    otel_logs_exporter = os.environ.get("OTEL_LOGS_EXPORTER", none)
    return otel_logs_exporter != none