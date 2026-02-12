import platform
from guardrails.classes.rc import RC
from guardrails.version import GUARDRAILS_VERSION
from guardrails_api.utils.has_internet_connection import has_internet_connection


def trace_server_start_if_enabled():
    config = RC.load()
    if config.enable_metrics is True and has_internet_connection():
        from guardrails.utils.hub_telemetry_utils import HubTelemetry

        HubTelemetry().create_new_span(
            "guardrails-api/start",
            [
                ("guardrails-version", GUARDRAILS_VERSION),
                ("python-version", platform.python_version()),
                ("system", platform.system()),
                ("platform", platform.platform()),
                ("arch", platform.architecture()[0]),
                ("machine", platform.machine()),
                ("processor", platform.processor()),
            ],
        )
