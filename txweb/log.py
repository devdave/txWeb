"""
    Currently just a stupid bridge between twisted.logger and user applications

"""
# from logging import getLogger as stdlib_getLogger, Logger
from twisted import logger


def getLogger(namespace: str = None) -> logger.Logger:
    """
        Just an adapted to mimic python's logging getLogger to twisted's Logger()
    :param namespace:
    :return:
    """
    return logger.Logger(namespace) if namespace else logger.Logger()