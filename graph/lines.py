from matplotlib import pyplot as plt
from collections.abc import Collection, Mapping


def plot_collection(*series):
    for s in series:
        if not isinstance(s, Collection):
            raise TypeError(f'Could not plot data from {type(s)}')
        if not all(isinstance(n, (int, float)) for n in s):
            raise TypeError(f'Could not plot data. One of values is neither int nor float.')
    fig = plt.Figure()
    for s in series:
        plt.plot(range(len(s)), tuple(s))
    return fig


def plot_mapping(**series):
    """
    assumes keys are labels, values are collections of values
    :param series: Mapping
    :return:
    """
    for k, v in series.items():
        if not isinstance(k, str):
            raise TypeError('Keys must be type str.')
        if not isinstance(v, Collection):
            raise TypeError(f'Could not plot data from "k" - value is type {type(v)}. Expected collection')
        if not all(isinstance(n, (int, float)) for n in v):
            raise TypeError(f'Could not plot "{k}" data. One of values is neither int nor float.')
    fig = plt.Figure()
    for k, v in series.items():
        plt.plot(range(len(v)), tuple(v), label=k)
    plt.legend()
    return fig


def plot_linear(*collections, **mappings):
    """
    plots linear data
    :param collections: Collection - collection of values to plot
    :param mappings: Mapping: {label: values}, where  label: str, and values: Collection[Union[int,float]]
    :return:
    """
    col_fig, map_fig = None, None
    if collections:
        col_fig = plot_collection(*collections)
    if mappings:
        map_fig = plot_mapping(**mappings)
    return col_fig, map_fig

