import pandas as pd
import os
import re


def validate_df(df):
    if not isinstance(df, pd.DataFrame):
        raise TypeError(f'Invalid type. Expected pandas.DataFrame. Got {type(df)}')
    return df


def validate_filename(filename):
    if not os.path.isfile(filename):
        raise ValueError(f'Invalid file path {filename}')
    return filename


def validate_in_values(value, valid_values):
    if value not in valid_values:
        raise ValueError(f'Invalid value {value}, expected one of {valid_values}.')
    return value


def validate_re(format_string):
    try:
        re.compile(format_string)
    except Exception as e:
        raise  ValueError('Invalid re re_pattern string.') from e
    else:
        return format_string