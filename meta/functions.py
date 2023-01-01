import inspect
import logging
from inspect import signature
from typing import Optional, Any, Container
from functools import wraps


def signature_parameters(obj):
    return tuple(signature(obj).parameters)


spar = signature_parameters  # alias


def in_module(module_):
    module_name = module_.__name__
    functions = inspect.getmembers(module_, inspect.isfunction)
    classes = inspect.getmembers(module_, inspect.isclass)
    #functions = [(fn_name, fn) for fn_name, fn in functions if fn.__module__ == module_name]
    #classes = [(class_name, cls) for class_name, cls in classes if cls.__module__  == module_name]
    return {'classes': classes, 'functions': functions}


def validate_value_in(obj: Any, container: Container, container_name: Optional[str] = None):
    if not hasattr(container, '__contains__'):
        raise AttributeError('Given container has no __contains__ method. Belonging condition can not be verified.')
    container_name = container_name or str(container)
    error_message = f'Object {obj} is not in {container_name}.'
    if obj not in container:
        raise
    return obj


def validate_type(obj: Any, type_: type):
    if not isinstance(type_, type):
        raise TypeError('type_ has to be type.')
    if not isinstance(obj, type_):
        raise TypeError(f'Invalid type {type(obj)}')
    return obj


def deprecated(fn):
    """
    a decorator to mark deprecated functions.
    A deprecated unction when called will issue warning each time when called.
    If it is called multiple times it will issue warining only once.
    """
    _called = False

    @wraps(fn)
    def wrapper(*args, **kwargs):
        nonlocal _called
        if not _called:
            logging.warning(f'Function {fn.__name__, repr(fn)} is deprecated. '
                            f'It is not serviced and might trigger errors or false results.')
        result = fn(*args, **kwargs)
        _called = True
        return result
    return wrapper

