from .metaloggers import MetaLogger
from functools import wraps, partial

obsolete_error_message_1 = "Invalid use of obsolete decorator. \
If used with argument this argument must be message type str"


def obsolete(arg):
    """
    this is a decorator.
    A decorated function, when called will issue a single warning.
    This decoratro can be called either with a parameter (message: str).
        This agrument value will be displayed in the warning message.
        If a parameter is not type str it will be cast to str.
    If left uncalled in code (will be called at time of decoration wwith the decorated function)
        - in this case only default wessage will show.
    """
    if callable(arg):
        return obsolete_decorator(arg)
    elif isinstance(arg, str):
        return partial(obsolete_decorator, message_appendix=arg)
    else:
        raise ValueError(obsolete_error_message_1)


def obsolete_decorator(fn, message_appendix=None):

    calls = 0
    logger = MetaLogger.logger
    message = f'Function {fn.__name__} is obsolete. It might be deactivated in the near future '
    if message_appendix:
        message = message + str(message_appendix)
    @wraps(fn)
    def wrapper(*args, **kwargs):
        nonlocal calls
        if calls == 0:
            logger.warning(message)
            calls = 1
        return fn(*args, **kwargs)

    return wrapper