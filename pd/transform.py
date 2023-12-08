import pandas as pd
import numpy as np
import re
from collections.abc import Iterable
from .validate import validate_df, validate_in_values, validate_re, validate_filename
from typing import Union, Any


def apply_nan(data: Union[np.ndarray, pd.DataFrame], nan: Any):
    """
    Changes declared value into numpy.nan in pandas.DataFrame or a numpy.ndarray

    :param data: numpy.ndarray | pandas.DataFrame
    :param nan: any value to be changed into numpy.nan in data
    :return:
    """
    if not isinstance(data, (pd.DataFrame, np.ndarray)):
        raise TypeError(f'function apply_nan can only transform pandas.DataFrame or numpy.ndarray')

    if nan is None and isinstance(data, pd.DataFrame):
        data[data.isna()] = np.nan
    else:
        data[data == nan] = np.nan
    return data


def drop_stray_rows(df: pd.DataFrame, drop_condition: callable, subset: Iterable = None, raise_ratio: float = 0.1):
    """
    Drops dataframe rows where condition applied to a cell value is True.

    df: pd.DataFrame
    condition: callable - must be a callable that returns bool type
    subset: IterableIf subset is declared, the condition is checked against the subset columns only.
    raise_ratio: float - decides if the resultant drop dataframe should raise a ValueError or return processed DataFrame

    :return: pd.DataFrame
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError(f'Expected pandas.DataFrame. Got {type(df)}')
    if len(df) < 1:
        return df

    if subset:
        if any(ss not in df.columns for ss in subset):
            raise ValueError(f'subset argument must be an iterable of df columns names')
        sdf = df[list(subset)]
    else:
        sdf = df

    if not isinstance(drop_condition(sdf.iat[0, 0]), bool):
        raise ValueError(f'drop_condition argument  must be a callable that returns bool type always.')

    bforedrop_len = df.shape[0]
    try:
        df = df[sdf[sdf.applymap(drop_condition)].isna().all(axis=1)]
    except TypeError as e:
        raise TypeError(f'drop_condition callable is not suitable for the data.') from e
    afterdrop_len = df.shape[0]
    if (bforedrop_len - afterdrop_len) / bforedrop_len > raise_ratio:
        raise ValueError(
            f'Too many stray rows in \n{df.head(5)}\n.\n.\n.\nshape={df.shape}\nAcceptable ratio is set to {raise_ratio}, but found more.')
    return df


def drop_valaues(df, value, axis=0):
    """
    Drops rows (if axis is set to 0) or columns (axis set to 1) containing indicated value
    :param df: pd.DataFrame
    :param value: Any
    :param axis: int (0 or 1)
    :return: transformed pd.DataFrame
    """
    dropable_i = set()
    dropable_c = set()
    for i in df.index:
        for c in df.columns:
            v = df.at[i, c]
            if v == value or v is value:
                (axis and dropable_c.add(c)) or dropable_i.add(i)
    if dropable_i:
        df = df.drop(list(dropable_i))
    if dropable_c:
        df = df.drop(list(dropable_c))
    return df


def find_incompatible(df, cal):
    """
    Identifies rows and columns where finds values not transformable by the callable
    Works only if callable thows exception if fails
    :param df: pd.DataFrame
    :param cal: any callable - cell value will be passed to it
    :return: identified values (v) together with indices (i) and columns (c)
    """
    identified = list()
    for i in df.index:
        for c in df.columns:
            v = df.at[i, c]
            try:
                cal(v)
            except:
                identified.append({'i': i, 'c': c, 'v': v})

    return identified

def fill_incompatible(df, callable, value_to_fill):
    """
    Identifies cells where finds values not transformable by the callable
    and replaces with value_to_fill
    Works only if callable thows exception when fails
    :param df:
    :param callable:
    :param value_to_fill:
    :return:
    """
    incompatibles = find_incompatible(df, callable)
    for inc in incompatibles:
        df.at[inc['i'], inc['c']] = value_to_fill
    return df


def column_from_filename(df, filename, target_column, re_pattern) -> pd.DataFrame:
    """
    Creates a column in the df based on re.search(re_pattern, filename)
    :param df: pd.DataFrame
    :param filename: str
    :param target_column: str name of category to be extracted : one of ('ward', 'microb', 'abx', 'year')
    :param re_pattern: str
    :return: df with ammended column names
    """
    df = validate_df(df)
    filename = validate_filename(filename)
    re_pattern = validate_re(re_pattern)

    try:
        column_value = re.search(re_pattern, filename).group()
    except Exception as e:
        raise ValueError(f'Could not extract from {filename} with {re_pattern}.') from e
    else:
        df[target_column] = column_value
    return df


def merge_cols(df: pd.DataFrame, columns, target_column, func=None):
    """

    :param df: pd.DataFrame to be transformed
    :param columns: list of columns, re.Pattern or string to construct re.Pattern .
        re.Pattern will be used to extract columns names to be merged
    :param target_column: str - column name after merger
    :param func: callable to ba applied over the rows values of the relevant columns (axis=1)
        default is lambda row: mean(row).
        (Mind, if some vales in the row are equal to np.nan, numpy funcfions like sum or mean will return np.nan)
    :return:
    """
    col_re = None
    if isinstance(columns, str):
       col_re = re.compile(columns)
    elif isinstance(columns, re.Pattern):
        col_re = columns
    elif isinstance(columns, Iterable) and all([isinstance(x, str) for x in columns]):
        pass
    else:
        raise ValueError('Read __doc__. Could not accept value columns.'
                         'Can only accept str, re.Pattern or a list of valid column names')
    if col_re:
        columns = [col for col in df.columns if col_re.search(col)]

    func = func or (lambda row: np.mean([val for val in row[~np.isnan(row)]]))

    newdf = pd.DataFrame()
    for col in [c for c in df.columns if c not in columns]:  # transport of irrelevant cols to newdf
        newdf[col] = df[col]
    newdf[target_column] = pd.Series([func(row) for row in df[columns].values])  # iteration over rows (0 axis of np.ndarray)

    return newdf

