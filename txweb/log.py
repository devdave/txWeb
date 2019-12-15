
from logging import getLogger as stdlib_getLogger, Logger

def getLogger(namespace: str) -> Logger:
    return stdlib_getLogger(namespace)