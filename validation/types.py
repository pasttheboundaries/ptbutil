from typing import Any, Type
from ptbutil.errors.basic import ValidationError


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
