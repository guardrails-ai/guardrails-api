import os
import logging
from opentelemetry._logs import set_logger_provider
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import SimpleLogRecordProcessor
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter

from src.modules.resource import resource

OTLP_ENDPOINT = os.environ.get('OTLP_ENDPOINT', 'http://localhost:4317')

# configure
__logger_provider = LoggerProvider(resource=resource)
set_logger_provider(__logger_provider)
__otlp_logs_exporter = OTLPLogExporter(endpoint=OTLP_ENDPOINT, insecure=True)
__logger_provider.add_log_record_processor(SimpleLogRecordProcessor(__otlp_logs_exporter))
__handler = LoggingHandler(level=logging.NOTSET, logger_provider=__logger_provider)
logging.root.setLevel(logging.NOTSET)

otel_logger = logging.getLogger('otel')
otel_logger.addHandler(__handler)