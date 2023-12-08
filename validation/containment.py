from .types import validate_type
from collections.abc import Collection
from ptbutil.errors import ValidationError, ContainmentError



def validate_in(object, collection, parameter_name=None, error_messag: str = None):

    validate_type(collection, Collection, parameter_name='collection',
                  error_message=f'parameter collection must be Collection, not {type(collection).__name__}')

    if parameter_name:
        parameter_name = f'Parameter {parameter_name}'
    else:
        parameter_name = 'Passed object'

    if object not in collection:
        raise ValidationError from ContainmentError(f'{parameter_name} not collection of valid objects.')

