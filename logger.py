from pythonjsonlogger import jsonlogger
import logging

def getHandler(**kwargs):
    handler = logging.StreamHandler()
    handler.setFormatter(jsonlogger.JsonFormatter(**kwargs))
    return handler

def getLogger(handlers=None, logging_level=logging.INFO):
    if handlers is None:
        handlers = [getHandler()]

    logger = logging.getLogger()
    for handler in handlers:
        logger.addHandler(handler)
    logger.setLevel(logging_level)
    return logger

logger = getLogger()
