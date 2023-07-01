
from .base import base_single_warning


def deprecated(fn):
    _message = 'is deprecated. It is not serviced and might trigger errors or produce false results.'
    return base_single_warning(fn, _message)

