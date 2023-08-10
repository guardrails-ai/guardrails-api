import os
import logging


def get_logger():
    log_level = os.environ.get("LOGLEVEL", logging.INFO)
    logging.basicConfig(level=log_level)
    return logging.getLogger("guardrails-api")


logger = get_logger()
