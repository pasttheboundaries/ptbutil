from .types import validate_type
from collections.abc import Collection
from ptbutil.errors import ValidationError, ContainmentError



def validate_in(obj, collection, parameter_name=None, error_message: str = None):

    validate_type(collection, Collection, parameter_name='collection',
                  error_message=f'parameter collection must be Collection, not {type(collection).__name__}')

    if parameter_name:
        parameter_name = f'Parameter {parameter_name}'
    else:
        parameter_name = 'Passed object'

    error_message = error_message or f'{parameter_name}  does not belong to the required collection: {collection}.'

    if obj not in collection:
        raise ValidationError from ContainmentError(error_message)

