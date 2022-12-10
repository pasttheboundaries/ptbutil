from matplotlib import pyplot as plt
from matplotlib.axes import SubplotBase
import numpy as np
from typing import Union, Iterable


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
