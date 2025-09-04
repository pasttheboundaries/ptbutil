from functools import wraps
from typing import Optional
from inspect import signature, _ParameterKind


def input_type_guard(_type, var_name: Optional[str] = None):
    if not isinstance(_type, type):
        raise TypeError(f'Expected type. Got {type(_type)}')
    if not var_name:
        raise ValueError(f'input_type_guard decorator requires ')
    def decorator(fn):
        params = signature(fn).parameters
        if var_name not in params:
            raise (f'var_name decorator parameter is invalid. Decorated function does not use {var_name} argument')
        args_names =[n for n, p in params.items() if p.kind == _ParameterKind.POSITIONAL_OR_KEYWORD or p.kind == _ParameterKind.POSITIONAL_ONLY]
        if var_name in args_names:
            i = args_names.index(var_name)
        else:
            i = 'missing'

        @wraps(fn)
        def wrapper(*args, **kwargs):
            if var_name in kwargs:
                arg = kwargs[var_name]
            else:
                if i == 'missing':
                    raise ValueError(f'could not determine guarded argument')
                arg = args[i]

            if not isinstance(arg, _type):
                raise TypeError(f'Argument {var_name} must be {_type}. Got {type(arg)}')
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
                raise TypeError(
                    f'Function {fn.__name__} is expected to return type {_type}, but returned illegal type: {type(result)}.')
            return result

        return wrapper

    return decorator

def type_wrap_output(_type):
    if not isinstance(_type, type):
        raise TypeError(f'Expected type. Got {type(_type)}')

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            result = fn(*args, **kwargs)
            return _type(result)
        return wrapper
    return decorator