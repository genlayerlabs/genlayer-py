"""Logging configuration for genlayer_py package."""

import logging


def setup_logger() -> logging.Logger:
    logger = logging.getLogger("genlayer_py")

    logger.setLevel(logging.NOTSET)
    logger.disabled = True

    logger.addHandler(logging.NullHandler())

    return logger


logger = setup_logger()

__all__ = ["logger"]
