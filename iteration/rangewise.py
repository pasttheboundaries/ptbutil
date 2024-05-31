"""
inspired by: advent of code 2023 day 5

Range and Multirange classes
"""

from collections.abc import Iterable
import math


class Range:

    """
    Range is a range of integers bordered by start and stop values. Stop value is not included in the range iteration.

    Instantiation:
    Accepts a pair or numbers for range start and stop values.
    If stop value is bigger than start - a ValueError is raised.

    Range methods:
        - union(other: Union[Range, Multirange]) - works as set.union. If ranges are disjoint return Multirange.
        - intersection(other: Union[Range, Multirange]) - as in set.intersection - if disjoint returns None
        - difference(other: Union[Range, Multirange]) - as in set.difference - if disjoint returns self
        - shift(v: int) - shifts the start ans stop values of the Range, by adding v, returns Range

    Supported operations:
        =, <, >, len, iter, indexing, slicing
        Indexing returns iteger, slicing returns range
    """
    def __init__(self, start=None, stop=None):
        if stop is None:
            if isinstance(start, Range):
                start, stop = start.start, start.stop
            else:
                start, stop = 0, start

        if any(not isinstance(n, int) for n in (start, stop)):
            raise TypeError('Range boundaries must be type int')

        if stop < start:
            raise ValueError(f'Stop index can not be lower than start: {(start, stop)}')

        self.start = start
        self.stop = stop

    def __add__(self, other):
        if not isinstance(other, self.__class__):
            raise TypeError(f'Could not add Range to {type(other)}')
        return Multirange(self, other)

    def __contains__(self, val):
        return self.start <= val < self.stop

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            raise TypeError(f'Could not compare Range to {type(other)}')
        return (self.start == other.start) and (self.stop == other.stop)

    def __getitem__(self, item):
        if isinstance(item, int):
            if (v := self.start + item) < self.stop:
                return v
            else:
                raise IndexError(f'{item}')
        elif isinstance(item, slice):
            return range(self.start, self.stop)[item]
        else:
            raise TypeError(f'{item}')

    def __gt__(self, other):
        if isinstance(other, int):
            return self.start > other
        elif isinstance(other, self.__class__):
            return self != other and not self < other
        else:
            raise TypeError(f'Can not compare {self.__class__} to {type(other)}.')

    def __hash__(self):
        return hash((self.start, self.stop))

    def __iter__(self):
        return (x for x in range(self.start, self.stop))

    def __len__(self):
        return self.stop - self.start

    def __lt__(self, other):
        if isinstance(other, int):
            return self.stop <= other

        if not isinstance(other, self.__class__):
            raise TypeError(f'Could not compare {self.__class__} to {type(other)}')
        if self.start == other.start:
            return self.stop < other.stop
        else:
            return self.start < other.start

    def __repr__(self):
        return f'<Range({self.start}:{self.stop})>'

    def bool(self):
        return self.start + 1 < self.stop

    def difference(self, other):
        if isinstance(other, Multirange):
            return other.difference(self)
        if not isinstance(other, self.__class__):
            raise TypeError(f'{type(other)}')

        if self.start == other.start:
            if self.stop <= other.stop:
                return None
            else:
                return Range(other.stop, self.stop)
        elif self.start < other.start:
            if self.stop <= other.start:
                return self
            else:
                if self.stop <= other.stop:
                    return Range(self.start, other.start)
                else:
                    return Multirange(Range(self.start, other.start), Range(other.stop, self.stop))
        elif self.start > other.start:
            if self.start >= other.stop:
                return self
            else:
                if self.stop > other.stop:
                    return Range(other.stop, self.stop)
                else:
                    return None
        else:
            raise NotImplemented

    def intersection(self, other):
        if isinstance(other, Multirange):
            return other.intersection(self)

        if not isinstance(other, self.__class__):
            raise TypeError(f'{type(other)}')

        start = max(self.start, other.start)
        stop = min(self.stop, other.stop)
        if start >= stop:
            return None
        else:
            return self.__class__(start, stop)

    def shift(self, v: int):
        if not isinstance(v, int):
            raise TypeError(f'Expected int. Got {v}')
        self.start += v
        self.stop += v

    def take_from(self, i: int):
        if not isinstance(i, int):
            raise TypeError('parameter i must be type int')
        if i not in self:
            return None
        else:
            return Range(i, self.stop)

    def take_upto(self, i: int):
        if not isinstance(i, int):
            raise TypeError('parameter i must be type int')
        if i not in self:
            return None
        else:
            return Range(self.start, i)

    def union(self, other):
        if isinstance(other, Multirange):
            return other.union(self)

        if not isinstance(other, self.__class__):
            raise TypeError(f'{type(other)}')

        if other.start >= self.stop or self.start >= other.stop:  # rozłączne
            return self + other

        start = min(self.start, other.start)
        stop = max(self.stop, other.stop)
        return self.__class__(start, stop)


class Multirange:
    """
    Multirange is a union type object of multiple Range objects.
    If Ranges included in the Multirange object overlap, they are reduced so all common elements are present.

    Instantiation accepts:
    - any even number of integers to indicate start and stop values of Ranges to be included
        eg:
        Multirange(2,4,7,9):
        will make 2 included ranges (2,4) and (7,9)
    - Range objects
    - Multirange objects



    methods:
        - union(other: Union[Range, Multirange]) - works as set.union. Returns Multirange.
        - intersection(other: Union[Range, Multirange]) - works as set.intersection. Returns Multirange.
        - shift(v: int) - shifts all Range objects by v. Returns Multirange.
    properties:
        - info - returns printable information

    supported operations:
        =, <, >, len, iter, indexing, slicing
        Indexing returns iteger, slicing returns range

    Slicing does not support stepped or inverse order slicing:
    [1:4:2] is illegal (stepped slicing)
    [6:3,-1] is illegal (stepped and inverse slicing)
    """

    def __add__(self, other):
        if isinstance(other, Range):
            ranges = self.ranges
            ranges.append(other)
        elif isinstance(other, self.__class__):
            ranges = self.ranges + other.ranges
        else:
            raise TypeError(f'Could not add Multirange and {type(other)}')
        return Multirange(*ranges)

    def __contains__(self, v):
        return any(v in r for r in self.ranges)

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            raise TypeError(f'{type(other)}')
        return self.ranges == other.ranges

    def __getitem__(self, item):
        if isinstance(item, int):
            if item < 0:
                i = len(self) + item
                if i >= 0:
                    return self[i]
                else:
                    raise IndexError(f'{item}')
            else:
                for r in self.ranges:
                    try:
                        return r[item]
                    except IndexError:
                        item = item - len(r)
                raise IndexError(f'{item}')

        elif isinstance(item, slice):
            if item.step is not None:
                raise ValueError('Multirange does not support stepped slicing.')
            start = item.start or 0
            stop = item.stop or len(self)
            if start < 0:
                start = len(self) + start
            if stop < 0:
                stop = len(self) + stop
            if start > stop:
                raise ValueError('Multirange does not support inverse order slicing.')
            return self._slice(start, stop)

    def __hash__(self):
        return hash(''.join(repr(r) for r in self.ranges))

    def _slice(self, start, stop):
        it = iter(self)
        for _ in range(start):
            next(it)
        for _ in range(start, stop):
            try:
                yield next(it)
            except StopIteration:
                return

    def __init__(self, *r):
        if all(isinstance(i, Range) for i in r):
            ranges = r
        elif all(isinstance(i, int) for i in r):
            if len(r) % 2 != 0:
                raise ValueError(f'Expected even number of elements if indexes are used for instantiation.')
            ranges = []
            for ind in range(0, len(r) - 1, 2):
                ranges.append(Range(r[ind], r[ind + 1]))
        elif all(isinstance(i, (Multirange, Range)) for i in r) :
            ranges = set()
            for i in r:
                if isinstance(i, Range):
                    ranges.add(i)
                elif isinstance(i, Multirange):
                    ranges = ranges.union(set(i.ranges))
                else:
                    raise RuntimeError('This code has a flaw here.')
        else:
            raise TypeError(f'Multirange requires int indices OR Range objects OR Multirange objects at instantiation.')
        self.ranges = sorted(self._reduce(ranges))

    def __iter__(self):
        for r in self.ranges:
            for e in range(r.start, r.stop):
                yield e

    def __len__(self):
        return sum(len(r) for r in self.ranges)

    def __lt__(self, other) -> bool:
        """
        compares start values , then stop values, then lengths
        """
        if not isinstance(other, self.__class__):
            raise TypeError(f'{type(other)}')
        if self.ranges[0].start == other.ranges[0].start:
            if self.ranges[-1].stop == other.ranges[-1].stop:
                return len(self) < len(other)
            else:
                return self.ranges[-1].stop < other.ranges[-1].stop
        else:
            return self.ranges[0].start < other.ranges[0].start

    def __repr__(self) -> str:
        template = '({}:{})'
        return f'<Multirange:{"".join((template.format(r.start, r.stop) for r in self.ranges))}>'

    def _reduce(self, ranges):
        ranges = sorted(ranges)
        r = ranges[0]
        try:
            other = ranges[1]
        except IndexError:
            return [r]

        if r.stop < other.start:  # not overlapping
            result = [r]
            result.extend(self._reduce(ranges[1:]))
            return result
        else:  # overlapping
            union = r.union(other)
            return self._reduce((union, *ranges[2:]))

    def difference(self, other):
        ranges = set()
        if isinstance(other, Range):
            for r in self.ranges:
                ranges.add(r.difference(other))
        if isinstance(other, Multirange):
            for r in self.ranges:
                for ro in other.ranges:
                    if r.intersection(ro):
                        ranges.add(r.difference(ro))
                    else:
                        ranges.add(r)
        ranges = {r for r in ranges if r}
        if not ranges:
            return None
        if len(ranges) == 1:
            return ranges.pop()
        return Multirange(*ranges)

    @property
    def info(self):
        x = self.ranges[-1].start
        x = math.ceil(math.log(x, 10))
        template = f"{{:{x}d}} - {{}}"
        return 'Multirange:\n' + '\n'.join((template.format(r.start, r.stop) for r in self.ranges))

    def intersection(self, other):
        if isinstance(other, Range):
            return self.intersection(self.__class__(other))
        elif isinstance(other, self.__class__):
            intersected = []
            for r in self.ranges:
                for ro in other.ranges:
                    if inter := r.intersection(ro):
                        intersected.append(inter)
                    else:
                        pass
            if not intersected:
                return None
            else:
                return self.__class__(*intersected)
        else:
            raise TypeError(f'{type(other)}')

    def shift(self, v: int):
        if isinstance(v, int):
            return Multirange(*[r.shift(v) for r in self.ranges])
        elif isinstance(v, Iterable):
            v = tuple(v)
            if not all(isinstance(s, int) for s in v):
                raise TypeError('Shift values must be int.')
            if not len(v) == len(self.ranges):
                raise ValueError(f'Got {len(v)} shift values but have {len(self.ranges)} ranges')
            for r, s in zip(self.ranges, v):
                r.shift(s)
            self.ranges = sorted(self._reduce(self.ranges))

    def take_from(self, i: int):
        ranges = []
        for r in self.ranges:
            if r < i:
                continue
            elif i in r:
                ranges.append(r.take_from(i))
            else:
                ranges.append(r)
        if ranges:
            if len(ranges) == 1:
                return ranges.pop()
            else:
                return Multirange(*ranges)
        else:
            return None

    def take_upto(self, i: int):
        ranges = []
        for r in self.ranges:
            if r < i:
                ranges.append(r)
            elif i in r:
                ranges.append(r.take_upto(i))
            else:
                continue
        if ranges:
            if len(ranges) == 1:
                return ranges.pop()
            else:
                return Multirange(*ranges)
        else:
            return None

    def union(self, other):
        if isinstance(other, Range):
            return self.union(Multirange(other))
        elif isinstance(other, Multirange):
            return self + other
        else:
            raise TypeError(f'{type(other)}')
