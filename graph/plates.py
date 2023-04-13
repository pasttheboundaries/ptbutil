from matplotlib import pyplot as plt
from matplotlib.axes import SubplotBase
import numpy as np
import pandas as pd
from typing import Union, Iterable, Any
from ptbutil.validation import validate_2d_array


__all__ = ['missing_data_plate','mdp' , 'plate2d']


class AbsentData:
    pass

def apply_nan(data: Union[np.ndarray, pd.DataFrame], nan: Any):
    data[data == nan] = np.nan
    return data


def _fix_types_in_DF(df):
    for column in df.columns:
        if df[column].dtype in (object, str):
            df[column] = df[column].apply(bool).apply(int)
    return df


def _fix_array_dtype(array):
    if array.dtype == object:
        array = (array == True).astype(int)
    return array


def missing_data_plate(data: Union[np.ndarray, pd.DataFrame], title=None, dpi=200, figsize=(4, 4), columns=None,
                       interpolation='antialiased', nans=AbsentData):
    """
    Visualises missing data in 2D data table like pandas.DataFrame or numpy.ndarray
    :param data: input data (numpy.ndarray or pandas.DataFrame);
    :param title: str ;
    :param dpi: int;
    :param figsize: tuple of 2 integers - size in inches ;
    :param columns: iterable of column names. If left None , ordinal numbers will be applied as in numpy.ndarray;
    :return: matplotlib.pyplot.Figure
    """


    # sorting types
    if isinstance(data, pd.DataFrame):
        data = _fix_types_in_DF(data)
    elif isinstance(data, np.ndarray):
        data = _fix_array_dtype(data)
    else:
        raise TypeError('Can only construct missing data plate for numpy.ndarray or pandas.DataFrame.')

    if isinstance(data, pd.DataFrame):
        columns = columns or data.columns
    else:
        columns = columns or list(range(data.shape[1]))

        data = validate_2d_array(data)
        data = pd.DataFrame(data)

    # changes declared nan values into np.nan, so it subsequently can be cut out by isna()
    if nans is AbsentData:
        nans = ('', None, np.nan)

    if isinstance(nans, (tuple, list, set)):
        for nan in nans:
            data = apply_nan(data, nan)
    else:
        data = apply_nan(data, nans)

    data = ~data.isna()
    data = data.values.astype(int)

    percentages = np.round((1 - (np.sum(data, axis=0) / data.shape[0])), 3)

    # this guarantees all ones will come out as black picture and avoids normalization
    # this must be done after percentages calculation
    if np.all(data == 1):
        data[0, 0] = 0.99991

    fig, axes = plt.subplots(dpi=dpi)
    fig.set_size_inches(figsize)
    axes.imshow(data, aspect='auto', cmap='binary', interpolation=interpolation)
    xtic_loc = range(0, data.shape[1])
    axes.set_xticks(xtic_loc, percentages, rotation=90, font={'size': 4})
    axes.set_xlim(-.5, data.shape[1] - 0.5)
    plt.xlabel('missing data fraction')
    axes2 = axes.twiny()
    axes2.set_xticks(xtic_loc, columns, rotation=90, font={'size': 4})
    axes2.set_xlim(-.5, data.shape[1] - 0.5)
    title and fig.suptitle(title)
    fig.tight_layout()
    return fig


mdp = missing_data_plate  # alias


def plate2d(*arrays: np.ndarray,
            shape: Union[tuple, int] = None,
            cmap='magma',
            interpolation: str = 'antialiased',
            size=1,
            dpi=200,
            skip_slots: Union[Iterable, int] = None
            ) -> plt.Figure:
    """

    Draws visualisation for numeric data in numpy.ndarray

    :param arrays: np.ndarray
    :param shape: tuple - shape of Figure to be drawn (rows, columns), or int: to indicate number of columns in one row
    :param cmap: matplotlib Colormap or string
    :param interpolation: str = 'antialiased'
    :param size: scaling factor for Figure
    :param dpi: int - dpi
    :param skip_slots: tuple of integers or integer to indicate Figure slots not to be drawn onto
        This might be usefull when drawing multiple rows to place related graphs one over another for comparison,
        if there are different numbers of related graphs to be ploted in rows.
    :return: Figure object

    """
    if not all(isinstance(array, np.ndarray) for array in arrays):
        raise TypeError('Can only draw plate for numpy.ndarray')

    if not all(array.ndim == 2 for array in arrays):
        raise ValueError('Can onlu draw plates for 2D numpy arrays.')



    if shape is None:
        shape = len(arrays)
    if isinstance(shape, int):
        shape = (1, shape)
    elif isinstance(shape, tuple):
        if len(shape) != 2:
            raise ValueError('Shape must be a tuple of 2 integers')
    else:
        raise TypeError('shape must be an integer or tuple of integers.')

    n_fields = shape[0] * shape[1]
    if not n_fields >= len(arrays):
        raise ValueError(f'Shape {shape} indicates {n_fields} fields, but {len(arrays)} are given.')

    if skip_slots:
        if isinstance(skip_slots, int):
            skip_slots = (skip_slots,)
        elif isinstance(skip_slots, tuple):
            if any(not isinstance(ind, int) for ind in skip_slots):
                raise TypeError('skip_slots must be a tuple of integers')
        else:
            raise TypeError('skip_slots must be a tuple of integers')
    else:
        skip_slots = tuple()

    # drawing
    fig, axes = plt.subplots(shape[0], shape[1], dpi=dpi)
    fig.set_size_inches((shape[1] * size, shape[0] * size))

    ### sorting axes structure
    if isinstance(axes, SubplotBase):
        axes = np.array([[axes]])
    if axes.ndim == 1:
        axes = axes.reshape(1, -1)

    array_i = 0
    slot_i = 0
    for row in range(shape[0]):
        for column in range(shape[1]):
            try:
                if skip_slots and slot_i in skip_slots:
                    raise IndexError
                array = arrays[array_i]
            except IndexError:
                fig.delaxes(axes[row][column])
                continue
            else:
                ax = axes[row, column]
                ax.get_xaxis().set_visible(False)
                ax.get_yaxis().set_visible(False)
                ax.imshow(array, aspect='auto', cmap=cmap, interpolation=interpolation)
                array_i += 1
            finally:
                slot_i += 1
            plt.tight_layout()
    return fig
