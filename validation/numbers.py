import math
from typing import Union, Type, Optional
from ptbutil.errors import ValidationError
from .types import validate_type


def _validate_number(
        examined_type: Type,
        value,
        parameter_name: str = None,
        min_value: Union[float, int] = -math.inf,
        max_value: Union[float, int] = math.inf,
        min_error_message: Optional[str] = None,
        max_error_message: Optional[str] = None
):


    if parameter_name:
        parameter_name = f'Parameter {parameter_name}'
    else:
        parameter_name = 'Value'

    validate_type(value, examined_type, error_message=f'{parameter_name} must be type int. Got {type(value)}')
    validate_type(min_value, int, float, error_message=f'min_value must be type float. Got {type(min_value).__name__}')
    validate_type(max_value, int, float, error_message=f'max_value must be type float. Got {type(max_value).__name__}')

    if value > max_value:
        raise ValidationError from ValueError(max_error_message or f'{parameter_name} must be less or equal {max_value}')
    if value < min_value:
        raise ValidationError from ValueError(min_error_message or f'{parameter_name} must be bigger or equal {min_value}')



def validate_int(
        value: int,
        parameter_name: str = None,
        min_value: Union[float, int] = -math.inf,
        max_value: Union[float, int] = math.inf,
        min_error_message: Optional[str] = None,
        max_error_message: Optional[str] = None
):
    return _validate_number(int,
                            value=value,
                            parameter_name=parameter_name,
                            min_value=min_value,
                            max_value=max_value,
                            min_error_message=min_error_message,
                            max_error_message=max_error_message)


def validate_float(
        value: float,
        parameter_name: str = None,
        min_value: Union[float, int] = -math.inf,
        max_value: Union[float, int] = math.inf,
        min_error_message: Optional[str] = None,
        max_error_message: Optional[str] = None
):
    return _validate_number(int,
                            value=value,
                            parameter_name=parameter_name,
                            min_value=min_value,
                            max_value=max_value,
                            min_error_message=min_error_message,
                            max_error_message=max_error_message)
