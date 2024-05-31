from typing import Any, Type, Iterable
from ptbutil.errors import ValidationError
import pandas as pd
import numpy as np


__all__ = ['validate_2d_array', 'validate_type']

def validate_type(obj: Any,
                  *types: Type,
                  parameter_name: str = None,
                  error_message: str = None):

    if parameter_name:
        parameter_name = f'Parameter {parameter_name}'
    else:
        parameter_name = 'Object'

    if not all(isinstance(t, type) for t in types):
        raise TypeError('One of declared types is not type. ')

    if not types:
        raise ValueError('types must be declared')

    if len(types) > 1:
        junction = 'one of'
    else:
        junction = ''

    error_message = error_message or f'{parameter_name} is of wrong type.' \
                                     f' Expected {junction}: {", ".join([t.__name__ for t in types])}'

    if all(not isinstance(obj, t) for t in types):
        raise ValidationError from TypeError(error_message)


def validate_2d_array(it: Iterable):
    if isinstance(it, np.ndarray):
        if it.ndim == 2:
            return it
        else:
            raise ValueError from ValidationError(f'Expected 2d array. Got {it.ndim}d array.')
    elif isinstance(it, pd.DataFrame):
        print('PANDAS')
        return it.values
    else:
        print('ELSE')
        try:
            return np.array(it)
        except Exception as e:
            raise ValidationError('Attempted to create numpy.array form delivered data but could not. Review input data') \
                from e