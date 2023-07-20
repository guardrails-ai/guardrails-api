import os
from logging import Logger, INFO

def getLogger():
    return Logger(os.environ["LOGLEVEL", INFO])

logger = getLogger()