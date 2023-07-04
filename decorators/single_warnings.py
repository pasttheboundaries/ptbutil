from functools import wraps
import logging
from types import FunctionType


DEPRECATED_MESSAGE = 'is deprecated. It is not serviced and might trigger errors or produce false results.'
EXPERIMENTAL_MESSAGE = 'is experimental. It is not validated and might trigger errors or produce false results.'


def base_single_warning(fn, _message):
    """
    a decorator to mark deprecated functions or classes
    .
    A warning will be issueed when:
    - the deprecated function is called,
    - or when the deprecated class is instantiated.
    If it is called multiple times it will issue warining only once.
    """
    _called = False

    @wraps(fn)
    def wrapper(*args, **kwargs):
        nonlocal _called
        if not _called:
            logging.warning(f'Function {fn.__name__, repr(fn)} {_message}')
            ('is deprecated. It is not serviced and might trigger errors or produce false results.')
            _called = True
        return fn(*args, **kwargs)

    def manipulate_class(fn):
        init = fn.__init__

        @wraps(init)
        def false_init(*args, **kwargs):
            nonlocal _called
            if not _called:
                logging.warning(f'Class {fn.__name__, repr(fn)} is deprecated. '
                                f'It is not serviced and might trigger errors or produce false results.')
                _called = True
            return init(*args, **kwargs)
        fn.__init__ = false_init
        return fn

    if isinstance(fn, FunctionType):
        return wrapper
    elif isinstance(fn, type):
        return manipulate_class(fn)
    else:
        raise TypeError('Missused decorator. Only FunctionType or type can be decorated.')


def deprecated(fn):
    _message = DEPRECATED_MESSAGE
    return base_single_warning(fn, _message)


obsolete = deprecated  # alias


def experimental(fn):
    _message = EXPERIMENTAL_MESSAGE
    return base_single_warning(fn, _message)
