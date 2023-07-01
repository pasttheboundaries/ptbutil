
from .base import base_single_warning


def experimental(fn):
    _message = 'is experimental. It is not validated and might trigger errors or produce false results.'
    return base_single_warning(fn, _message)
