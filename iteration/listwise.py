from collections.abc import Iterable, Callable, Sequence, Generator
from typing import Optional, NoReturn
from itertools import chain, product
from collections import deque
import numpy as np


def chaintype(t: type, *iterators: Iterable):
    """
    works as itertools.chain but does not apply iteration over elements of sertain types
    :return: mapping
    """
    return chain(*map(lambda x: (x,) if isinstance(x, t) else x, iterators))


def each_with_each(*iterables):
    """this function is actually faster than itertools.product"""
    if len(iterables) == 1:
        return ((i,) for i in iterables[0])
    first = iterables[0]
    rest = iterables[1:]
    return (tuple((i,*j)) for i in first for j in each_with_each(*rest))


def flatlist(l) -> list:
    """flattens nested lists"""
    items = []
    for item in l:
        if isinstance(item, (tuple, list, set)):
            items += flatlist(item)
        else:
            items.append(item)
    return items


class GridFeed:
    """GridFeed is an object that lazily reconfigures dict of lists into list of single valued dicts
    containing permutations of original values. GridFeed is an iterable, it has __iter__ method.
    Attributres:
        collections: dict - input data - a dictionary of lists
        combinations : list - output data - a list of dinglevalued dictionaries that are permutations of collections."""
    def __init__(self, collections):
        if isinstance(collections, dict):
            if all([isinstance(v, Iterable) for k, v in collections.items()]):
                self.collections = [value for key, value in collections.items()]
                self.keys = [key for key, value in collections.items()]
                self.combinations = ({key: value for key, value in zip(self.keys, set_)} for set_ in
                                     product(*self.collections))
            else:
                raise TypeError(f'One of passed values is not an iterable')
        elif isinstance(collections, GridFeed):
            self.collections = collections.collections
            self.keys = collections.keys
            self.combinations = collections.combinations
        else:
            raise TypeError(f'Passed type {type(collections)}. '
                            f'Expected tuple, list, set or dictionary of iterables.')

    def __iter__(self):
        return ({key: value for key, value in zip(self.keys, set_)} for set_ in product(*self.collections))

    def __len__(self):
        return len(tuple(iter(self)))


def indmap(fn, sequence, indices=None):
    """maps function to a sequence elements indicated in indices.
    :param fn: cal that accepts one argument and returns resulting object,
    :param sequence: any Sequence type,
    :param indices: any Collection type with integer indexes.
    """
    if not isinstance(sequence, Sequence):
        raise TypeError('sequences must be Sequence type. This means it has to have __getitem__ method implemented.')
    if not isinstance(fn, Callable):
        raise TypeError('fn (function) must ba a Callable type.')
    if not indices:
        yield from sequence
        return
    elif any(not isinstance(ind, int) for ind in indices):
        raise ValueError('indices must be a collection of integers.')
    else:
        l = len(sequence)
        ind = 0
        while ind < l:
            if ind in indices:
                yield(fn(sequence[ind]))
            else:
                yield sequence[ind]
            ind += 1


class MaskableList(list):
    def __init__(self, lista=None):
        if lista is None:
            lista = []
        if not isinstance(lista, list):
            raise TypeError('Passed object is not list.')
        [self.append(x) for x in lista]

    def mask(self, m, reduce=False):
        if not isinstance(m, Iterable):
            raise TypeError(f'Mask must be iterable. Received: {m}')
        if type(m) == str:
            m = [e.replace('0','').replace(' ','') for e in m]
        m = [bool(el) for el in m]
        prod = lambda x, y: x if y else None
        if reduce:
            return(pair[0] for pair in zip(self, m) if pair[1])
        return (prod(*pair) for pair in zip(self, m))


class UnevenNestingError(Exception):
    pass


class Nesting:
    """
        this class calculates nesting of iterables

        :param iterables: nested iterables
        :param nested_type: default is str, a type that will be considered token and not counted as a nested iterable
        :param _n: this is a meta parameter and should not be altered or used by user
        :return: int number depicting nesting depth (equivalent of np.ndarray.ndim)
        :raises: UnevenNestingError if uneven nesting found
    """
    def __init__(self, iterables: Iterable,
                 nested_type: Optional[type] = None,
                 nesting_type: Optional[type] = None):
        self.iterables = iterables

        if nested_type:
            self._validate_entry_types(nested_type, 'nested_type')
        self.nested_type = nested_type

        if nesting_type:
            self._validate_entry_types(nesting_type, 'nesting_type')
        self.nesting_type = nesting_type

        self.common_iteration_types = (list, tuple, set, dict, np.ndarray, Iterable, Sequence, Generator)
        self.common_non_iteration_types = (int, float, str, bool, None, np.str_)

        self.nesting = self._nesting(self.iterables)

    @staticmethod
    def _validate_entry_types(entry_type, parameter_name) -> NoReturn:
        message = f'{parameter_name} must be type or tuple of types.'
        if isinstance(entry_type, (tuple, list)):
            if not all(isinstance(t, type) for t in entry_type):
                raise TypeError(message)
        elif not isinstance(entry_type, type):
            raise TypeError(message)
        else:
            pass

    def _check_nesting_type(self, type_: type) -> bool:
        """checks if passed type is a nesting type"""
        if self.nesting_type:
            if isinstance(self.nesting_type, (tuple, list)):
                if any(type_ == nt for nt in self.nesting_type):
                    return True
                else:
                    return False
            else:
                if type_ == self.nesting_type:
                    return True
                else:
                    return False
        else:
            if any(type_ == cit for cit in self.common_iteration_types):
                return True
            else:
                return False

    def _check_nested_type(self, type_: type) -> bool:
        """checks if passed type is a nested type"""
        if self.nested_type:
            if isinstance(self.nested_type, (tuple, list)):
                if any(type_ == nt for nt in self.nested_type):
                    return True
                else:
                    return False
            else:
                if type_ == self.nested_type:
                    return True
                else:
                    return False
        else:
            if any(type_ == cnit for cnit in self.common_non_iteration_types):
                return True
            else:
                return False

    def _nesting(self, iterables: Iterable, _n=0) -> int:
        if self.nested_type:
            if self._check_nested_type(type(iterables)):
                return _n
            elif self._check_nesting_type(type(iterables)):  # possibly nesting_type:
                if all(self._check_nested_type(type(token)) for token in iterables):
                    return _n + 1
                else:
                    inner_types = {type(token) for token in iterables}
                    if len(inner_types) == 0:
                        return _n + 1
                    elif len(inner_types) == 1:
                        type_ = inner_types.pop()
                        if self._check_nesting_type(type_):
                            nestings_ = {self._nesting(token, _n=_n + 1) for token in iterables}
                            if len(nestings_) > 1:
                                raise UnevenNestingError('Uneven _nesting. Check data')
                            else:
                                return nestings_.pop()
                        else:
                            raise TypeError(f'Unsuported nested type or the found type has not been declared. '
                                            f'Found {str(type_)} type')
                    else:
                        raise UnevenNestingError(f'Data contain various types or uneven nesting used.'
                                                 f' Can only accept evenly nested Iterables of strings.'
                                                 f' Types {str(inner_types)} have been found at the same level.')
            else:
                raise TypeError(f'Unresolved type {type(iterables)}. '
                                f'Most likely bot nesting_type and nested_type have been declared, '
                                f'and type {type(iterables)} has not been included.')

        else:
            if self._check_nesting_type(type(iterables)):  # possibly nesting_type:
                if all(not self._check_nesting_type(type(token)) for token in iterables):  # none inner is nesting
                    return _n + 1  # so probbably all innner are nested
                else:  # at least one inner is nesting
                    inner_types = {type(token) for token in iterables}
                    if len(inner_types) == 0:
                        return _n + 1
                    elif len(inner_types) == 1:
                        type_ = inner_types.pop()
                        if self._check_nesting_type(type_):
                            nestings_ = {self._nesting(token, _n=_n + 1) for token in iterables}
                            if len(nestings_) > 1:
                                raise UnevenNestingError('Uneven _nesting. Check data')
                            else:
                                return nestings_.pop()
                        else:
                            raise TypeError(f'Unsuported nested type or the found type has not been declared. '
                                            f'Found {str(type_)} type.')
                    else:
                        raise UnevenNestingError(f'Data contain various types or uneven nesting used.'
                                                 f' Can only accept evenly nested Iterables of strings.'
                                                 f' Types {str(inner_types)} have been found at the same level.')
            else:  # not nesting type -> so possibly nested type
                self.nested_type = list()
                self.nested_type.append(type(iterables))
                return _n


def nesting(iterables, nested_type: Optional[type] = None, nesting_type: Optional[type] = None):
    """
    this function calculates nesting of iterables

        :param iterables: nested iterables
        :param nested_type: default is str, a type that will be considered token and not counted as a nested iterable
        :param _n: this is a meta parameter and should not be altered or used by user
        :return: int number depicting nesting depth (equivalent of np.ndarray.ndim)
        :raises: UnevenNestingError if uneven nesting found
    """
    return Nesting(iterables=iterables, nested_type=nested_type, nesting_type=nesting_type).nesting


def ngrams(iterable: Iterable, n: int = 1):
    if not isinstance(n, int):
        raise TypeError('ngrams parameter must be type int.')
    if n < 1:
        raise ValueError ('ngrams parameter must be bigger than 0.')
    if not isinstance(iterable, Iterable):
        raise TypeError('iterable argument must be Iterable type.')
    iterable = chain(iterable, [None] * (n - 1))
    window = deque([None] * (n - 1), maxlen=n)
    iterable = iterable.__iter__()
    while True:
        try:
            window.append(next(iterable))
            yield tuple(window)
        except StopIteration:
            break


def nlen(*iterables):
    """przyjmuje dowolną liczbę argumentów
    zwraca długości wszystkich argumentów
    """
    return tuple((len(i) for i in iterables))


def sequence_binary_mask(sequence, binary_mask: int = 0):
    """returns a generator of elements from sequence masked with a binary number.
    Binary mask is read from right, but sequence  is read from left.
    sequence = 'abcde' and mask = 0b1101 will return (a,c,d).
    :param binary_mask: can be any positive integer"""
    ind = 0
    l = len(sequence)
    while ind < l:
        if binary_mask >> ind & 1:
            yield sequence[ind]
        else:
            pass
        ind += 1


class Stack(list):
    """Classical stack object with maximum size declaration.
    For bidirectional object find collections.deque"""
    def __init__(self, lista=None, max_size=100):
        super().__init__()
        lista = lista or []
        if not isinstance(lista, list):
            raise TypeError('Passed object is not list.')
        self.max_size = max_size
        [self.append(x) for x in lista]

    def append(self, item):
        if len(self) >= self.max_size:
            self.pop(0)
        super().append(item)

