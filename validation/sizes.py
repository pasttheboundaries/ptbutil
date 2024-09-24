from ptbutil.errors import ValidationError
from typing import Collection, Optional


def validate_len(obj: Collection,
                 min_len: int,
                 max_len: int,
                 parameter_name: Optional[str] = None,
                 min_error_message: Optional[str] = None,
                 max_error_message: Optional[str] = None
                 ):
    if parameter_name:
        parameter_name = f'Parameter {parameter_name}'
    else:
        parameter_name = 'Object'

    min_error_message = min_error_message or f'{parameter_name} can not be less than {min_len}'
    max_error_message = max_error_message or f'{parameter_name} can not be more than {min_len}'


    if not hasattr(obj, '__len__'):
        raise ValidationError(f'object {obj} has no __len__ method.')

    if len(obj) < min_len:
        raise ValidationError(min_error_message)

    if len(obj) > max_len:
        raise ValidationError(max_error_message)


def validate_lt():
    pass

def validate_gt():
    pass

def validate_le():
    pass

def validate_ge():
    pass
