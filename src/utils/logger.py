import os
import logging
from typing import Optional

log_levels = {
    "CRITICAL": 50,
    "ERROR": 40,
    "WARNING": 30,
    "INFO": 20,
    "DEV": 15,
    "DEBUG": 10,
    "NOTSET": 0,
}


def get_log_level(log_level: Optional[str] = "INFO") -> int:
    return log_levels.get(log_level, log_levels["INFO"])


def get_logger():
    log_level = get_log_level(os.environ.get("LOGLEVEL"))
    logging.basicConfig(level=log_level)
    return logging.getLogger("guardrails-api")


logger = get_logger()

dev_stream_handler = logging.StreamHandler()
dev_stream_handler.setLevel(log_levels["DEV"])
logger.addHandler(dev_stream_handler)


def log_dev(msg: str = ""):
    logger.log(log_levels["DEV"], msg)


logger.__setattr__("dev", log_dev)
