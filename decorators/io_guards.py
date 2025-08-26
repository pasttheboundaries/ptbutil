from functools import wraps
from typing import Optional
from inspect import signature


def input_type_guard(_type, var_name: Optional[str] = None):
    if not isinstance(_type, type):
        raise TypeError(f'Expected type. Got {type(_type)}')

    def decorator(fn):
        params = signature(fn).parameters
        if var_name and var_name not in params:
            raise (f'var_name decorator parameter is invalid. Decorated function does not {var_name} argument')
        else:
            ind = list(params.keys()).index(var_name)

        @wraps(fn)
        def wrapper(*args, **kwargs):
            if var_name:
                if var_name in kwargs:
                    arg = kwargs[var_name]
                else:
                    arg = args[ind]

                if not isinstance(arg, _type):
                    raise TypeError(f'Argument {var_name} must be {_type}. Got {type(arg)}')
                else:
                    return fn(*args, **kwargs)
        return wrapper
    return decorator


def output_type_guard(_type):
    if not isinstance(_type, type):
        raise TypeError(f'Expected type. Got {type(_type)}')

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            result = fn(*args, **kwargs)
            if not isinstance(result, _type):
                raise TypeError(f'Function {fn.__name__} is expected to return type {_type}, but returned illegal type: {type(result)}.')
            return result
        return wrapper
    return decorator

