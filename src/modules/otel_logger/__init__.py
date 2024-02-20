# !!! UPDATE ME !!!
# See Tracer setup
import os
import logging
import opentelemetry._logs as logs
# from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import (
    BatchLogRecordProcessor,
    ConsoleLogExporter,
    # SimpleLogRecordProcessor,
)
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter


OTEL_EXPORTER_OTLP_ENDPOINT = os.environ.get(
    "OTEL_EXPORTER_OTLP_ENDPOINT", "http://otel-collector:4317"
)

logger_provider = logs.get_logger_provider()
otlp_logs_exporter = OTLPLogExporter(
    endpoint=OTEL_EXPORTER_OTLP_ENDPOINT, insecure=True
)
console_log_exporter = ConsoleLogExporter()
logger_provider.add_log_record_processor(
    BatchLogRecordProcessor(otlp_logs_exporter)
)
# For Debugging
# logger_provider.add_log_record_processor(SimpleLogRecordProcessor(otlp_logs_exporter))
# logger_provider.add_log_record_processor(SimpleLogRecordProcessor(console_log_exporter))
log_level = os.environ.get("LOGLEVEL", logging.INFO)
logging.root.setLevel(log_level)

service_name = os.environ.get("OTEL_SERVICE_NAME", "guardrails-api")
logger = logging.getLogger(service_name)
