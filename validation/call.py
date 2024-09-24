from collections.abc import Callable
from .types import validate_type
from ptbutil.errors import ValidationError


def validate_with_callable(obj: object, call: Callable, parameter_name=None, error_message: str = None):
    validate_type(call, Callable, parameter_name='call',
                  error_message=f'parameter call must be Callable, not {type(call).__name__}')

    if parameter_name:
        parameter_name = f'Parameter {parameter_name}'
    else:
        parameter_name = 'Passed object'

    error_message = error_message or f'{parameter_name} got invalid object.'

    res = call(obj)
    validate_type(res, bool, error_message=f'Call must return bool. Got {type(res)}.')

    if not res:
        raise ValidationError(error_message)