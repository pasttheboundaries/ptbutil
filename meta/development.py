from .metaloggers import MetaLogger
from functools import wraps, partial

error_message_1 = "Invalid use of obsolete decorator. \
If used with argument this argument must be message type str"

def in_development(arg):
    if callable(arg):
        return developed_decorator(arg)
    elif isinstance(arg, str):
        return partial(developed_decorator, message_appendix=arg)
    else:
        raise ValueError(error_message_1)


def developed_decorator(fn, message_appendix=None):

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