import os
import logging

def getLogger():
    log_level = os.environ.get("LOGLEVEL", logging.INFO)
    logging.basicConfig(level=log_level)
    return logging.getLogger("guardrails-api")

logger = getLogger()