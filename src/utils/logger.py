import os
import logging
# Shouldn't need this with auto-instrumentation
# from src.modules.otel_logger import handler as otel_handler


def get_logger():
    log_level = os.environ.get("LOGLEVEL", logging.INFO)
    logging.basicConfig(level=log_level)
    return logging.getLogger("guardrails-api")


logger = get_logger()
# logger.addHandler(otel_handler)
