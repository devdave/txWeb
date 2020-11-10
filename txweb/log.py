
# from logging import getLogger as stdlib_getLogger, Logger
from twisted import logger


def getLogger(namespace: str = None) -> logger.Logger:
    return logger.Logger(namespace) if namespace else logger.Logger()