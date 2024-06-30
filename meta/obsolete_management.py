import logging
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
        return _obsolete_decorator(arg)
    elif isinstance(arg, str):
        return partial(_obsolete_decorator, message_appendix=arg)
    else:
        raise ValueError(obsolete_error_message_1)


def _obsolete_decorator(fn, message_appendix=None):
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(message)s')
    handler.setFormatter(formatter)
    logger = logging.getLogger('indentation_debug_logger')
    logger.addHandler(handler)

    called = False
    message = f'Function {fn.__name__} is obsolete. It might be deactivated in the near future. '
    if message_appendix:
        message = message + str(message_appendix)

    @wraps(fn)
    def wrapper(*args, **kwargs):
        nonlocal calls
        if called:
            logger.warning(message)
            called = True
        return fn(*args, **kwargs)

    return wrapper


def deprecated(fn):
    """
    a decorator to mark deprecated functions.
    A deprecated unction when called will issue warning when called.
    If it is called multiple times it will issue warining only once.
    """
    called = False

    @wraps(fn)
    def wrapper(*args, **kwargs):
        nonlocal called
        if not called:
            logging.warning(f'Function {fn.__name__, repr(fn)} is deprecated. '
                            f'It is not serviced and might trigger errors or false results.')
        result = fn(*args, **kwargs)
        called = True
        return result
    return wrapper