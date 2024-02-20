import os
import logging

# Shouldn't need this with auto-instrumentation
# from src.modules.otel_logger import handler as otel_handler


def get_logger():
    log_level = os.environ.get("LOGLEVEL", logging.INFO)
    logging.basicConfig(level=log_level)
    _logger = logging.getLogger("guardrails-api")
    # _logger.addHandler(otel_handler)
    return _logger


logger = get_logger()
