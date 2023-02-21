from .metaloggers import MetaLogger
from functools import wraps, partial


error_message_1 = "Invalid use of obsolete decorator. \
If used with argument this argument must be message type str"


def in_development(arg):
    """
    Functions that are in development migt be decorated with this
    Single warning will be issued.
    It can be used with parameter type str. Tu be appended to the warning message.
    :param arg:
    :return:
    """
    if isinstance(arg, type):  # TODO class managenment
        return arg
    elif callable(arg):
        return _developed_decorator(arg)
    elif isinstance(arg, str):
        return partial(_developed_decorator, message_appendix=arg)
    else:
        raise ValueError(error_message_1)


def _developed_decorator(fn, message_appendix=None):

    calls = 0
    logger = MetaLogger.logger
    message = f'Function {fn.__name__} is in development. '
    if message_appendix:
        message = message + message_appendix
    @wraps(fn)
    def wrapper(*args, **kwargs):
        nonlocal calls
        if calls == 0:
            logger.warning(message)
            calls = 1
        return fn(*args, **kwargs)

    return wrapper