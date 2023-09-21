from functools import wraps
from src.modules.otel_meter import otel_meter

request_total = otel_meter.create_counter("http_requests")
requests_over_time = otel_meter.create_histogram(
        name="http_requests_per",
        description="request time series"
    )
# status_2xx_counter = otel_meter.create_counter("2xx_statuses")
# status_4xx_counter = otel_meter.create_counter("4xx_statuses")
# status_5xx_counter = otel_meter.create_counter("5xx_statuses")


def gather_request_metrics(fn):
    @wraps(fn)
    def decorator(*args, **kwargs):
        request_total.add(1)
        requests_over_time.record(1)
        return fn(*args, **kwargs)

    return decorator
