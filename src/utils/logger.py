import os
from logging import Logger, INFO

def getLogger():
    log_level = os.environ.get("LOGLEVEL", INFO)
    return Logger(log_level)

logger = getLogger()