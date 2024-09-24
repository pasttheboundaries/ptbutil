"""
this module provides RedInfoLogger
it is a subclass of logging.Logger
it prints out red messages, looking like warning message

"""

import logging
from logging.handlers import RotatingFileHandler
from typing import Optional


class CustomFormatter(logging.Formatter):
    def __init__(self, header: Optional[str] = None):
        super().__init__()
        if header:
            header = header + ': '
        self.header = header or  ''
    def format(self, record):
        # Only include the message

        return self.header + record.getMessage()


def get_info_logger(name, header: Optional[str] = None):
    name = '_'.join((name, 'RED_INFO'))
    logger = logging.getLogger(name)
    logger.setLevel(logging.WARNING)
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    red_h = logging.StreamHandler()
    red_h.setFormatter(CustomFormatter(header))
    logger.addHandler(red_h)

    def log(message):
        logger.warning(message)

    logger.log = log

    return logger


def get_file_logger(log_file, logger_name, *, tag=None, log_level=logging.INFO):

    """
    This factory creates a custom file logger that can be used throughout the whole environment once instantiated.
    Its intended use is as follows:
        1. In you start scrip use:
        get_file_logger(LOGGER_PATH, LOGGER_NAME)  # no need to ascribe to a variable unless needed in this start script

        2. In any other module working in under the same globals or being imported by the start script use:
        logger = logging.getLogger(LOGGER_NAME)  # this will be the same logger as set up in the sart script



    :param log_file: str - log file path
    :param tag: str - tag to be included in the message
    :param logger_name: str: logger name (see above.)
    :param log_level: default is logging.INFO
    :return: logging.Logger
    """

    # Create a logger
    logger = logging.getLogger(logger_name)
    logger.setLevel(log_level)

    # Create a file handler that logs even debug messages
    file_handler = RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5)
    file_handler.setLevel(log_level)

    # Create a formatter and add it to the handler
    if tag:
        tag = f'{tag}:'
    else:
        tag = ''
    formatter = logging.Formatter(f'{tag}%(asctime)s: %(message)s')
    file_handler.setFormatter(formatter)

    # Add the handler to the logger
    logger.addHandler(file_handler)

    return logger

