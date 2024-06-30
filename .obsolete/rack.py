"""
This is experimental
the code is inefficient however interesting and might be used in the future
"""
from math import log
import json
from typing import Any, Mapping, Generator


class IndexOccupiedException(Exception):
    pass


class BinaryMultiindex:
    """
    multiindex holds a digit that maps key integers to indices

    mapped indices reflect the order of the integer keys:
    ie:
    if keys are (1,3,5) -> related indices are (0,1,2)
    if key 4 is added:
    (1,3,4,5) -> relevant indicees are (0,1,2,3) and the order is maintained
    so key 4 will be indexed to 2.
    The binary coding for this is stored as a digit
    So this only makes sense for small value keys.
    ie:
    number 5 holds keys 0 and 2 (2**0 and 2**2) that will be indexed (0,1)

    usage:
    bi = BinaryMultiindex(9)  # binary encoded = 0b1001

    bi.number(0) # = 0
    bi.number(1) # = 3
    bi.index(0) # = 0
    bi.index(3) # = 1

    bi.insert(1) # binary encoded 0b1011
    bi.number(1) # = 1
    bi.index(1) # = 1
    bi.number(2) # = 3
    bi.index(3) # = 2


    disadvantages:
    - difficult to wrap you head around.
    - never seemd usefull, never used it
    """

    def __init__(self, value=0):
        self.value = value

    def iter_bits(self) -> Generator:
        i = 0
        n = int(self.value)
        while n:
            v = n & 1
            yield v
            n >>= 1

    def insert(self, n) -> None:
        """
        inserts new key number to BM
        """
        if self.value & 2 ** n:
            raise IndexOccupiedException(f'Index {n} is aleady occupied.')
        self.value |= (2 ** n)

    def index(self, n) -> int:
        """
        translates key number to index if in BM instance
        """
        i = -1
        value = int(self.value)
        ind = -1
        while i < n:
            i += 1
            tru = bool(value & 1)
            ind += tru and 1
            value >>= 1
        return tru and ind

    def number(self, n) -> int:
        """
        translates index to key nymber if in BM instance
        """
        steps = log(self.value, 2) + 1
        i = -1
        value = int(self.value)
        ind = -1
        while i < steps:

            i += 1
            # tru = bool(value & 1)
            ind += value & 1 and 1
            if ind == n:
                return i
            value >>= 1
        return False

    def __len__(self) -> int:
        return sum(tuple(self.iter_bits()))


class RackFrozenError(Exception):
    def __str__(self):
        return 'Operation can not be performed. The Rack is frozen.'


class RackDeserializationError(Exception):
    pass


class Rack:
    """
    this is a mapping class that uses BinaryMultiindex for indexing
    its inner structure is :
    (miltiindex, tuple_of_content)

    it is less efficient than dict !!
    """

    def __init__(self) -> None:
        self.multiindex = BinaryMultiindex()
        self.shelves = list()
        self.frozen = False

    def __getitem__(self, item) -> Any:
        ind = self.multiindex.index(item)
        return isinstance(ind, int) and (not isinstance(ind, bool)) and self.shelves[ind]

    def __setitem__(self, item, value) -> None:
        if self.frozen:
            raise RackFrozenError
        try:
            self.multiindex.insert(item)
            ind = self.multiindex.index(item)
            self.shelves.insert(ind, value)
        except IndexOccupiedException:
            ind = self.multiindex.index(item)
            self.shelves[ind] = value

    def items(self) -> Generator:
        for n in range(round(log(self.multiindex.value, 2)) + 1):
            if v := self[n]:
                yield n, v

    def freeze(self) -> None:
        """
        freezes Rack (turns all lists into tuples)
        :return:
        """
        self.shelves = tuple(self.shelves)
        for shelf in self.shelves:
            if isinstance(shelf, Rack):
                shelf.freeze()
        self.frozen = True

    def try_serialize(self, obj) -> Any:
        if isinstance(obj, self.__class__):
            return obj.serializable
        else:
            return obj

    @property
    def serializable(self) -> tuple:
        shelves = [self.try_serialize(obj) for obj in self.shelves]
        return (self.__class__.__name__, self.multiindex.value, tuple(shelves))
        # return (self.multiindex.value, tuple(shelves))

    @classmethod
    def try_deserialize(cls, ser) -> Any:
        try:
            return cls.deserialize(ser)
        except RackDeserializationError as e:
            # print('trying deserialize', ser, type(ser))
            # if isinstance(ser, tuple):
            #     raise e
            return ser

    #     # this is deserialization if serialization uses 2 element tuple = does not use self.__class__.__name__ notation
    #     @classmethod
    #     def deserialize(cls, ser):
    #         if not isinstance(ser, (tuple, list)):
    #             raise RackDeserializationError from TypeError(f'Expected type tuple. Got: {type(ser)}')
    #         if not len(ser) == 2:
    #                 raise RackDeserializationError from ValueError('Invalid length of the input tuple.')

    #         multiindex, shelves = ser
    #         if not isinstance(multiindex, int):
    #             raise RackDeserializationError from TypeError('Multiindex code must be type int.')
    #         if not isinstance(shelves, (tuple, list)):
    #             raise RackDeserializationError from TypeError(f'Last item of the passed tuple was expected to be type tuple or list. Got {type(shelves)}.')
    #         multiindex = BinaryMultiindex(multiindex)
    #         if len(shelves) != len(multiindex):
    #             raise RackDeserializationError from ValueError(f'Multiindex {multiindex.value}, len={len(multiindex)} incompatible with the shelves (len={len(shelves)}).')

    #         shelves = [Rack.try_deserialize(s) for s in shelves]
    #         rack = cls()
    #         rack.multiindex = multiindex
    #         rack.shelves = shelves
    #         return rack

    @classmethod
    def deserialize(cls, ser):
        if not isinstance(ser, (tuple, list)):
            raise RackDeserializationError from TypeError(f'Expected type tuple. Got: {type(ser)}')
        if len(ser) == 3:
            if not ser[0] == cls.__name__:
                raise RackDeserializationError from ValueError(
                    f'Unsure of the input value. Value 0 expected to be str={cls.__name__}. Got {ser[0]}')
            ser = ser[1:]
        if not len(ser) == 2:
            raise RackDeserializationError from ValueError('Invalid length of the input tuple.')

        multiindex, shelves = ser
        if not isinstance(multiindex, int):
            raise RackDeserializationError from TypeError('Multiindex code must be type int.')
        if not isinstance(shelves, (tuple, list)):
            raise RackDeserializationError from TypeError(
                f'Last item of the passed tuple was expected to be type tuple or list. Got {type(shelves)}.')
        multiindex = BinaryMultiindex(multiindex)
        if len(shelves) != len(multiindex):
            raise RackDeserializationError from ValueError(
                f'Multiindex {multiindex.value}, len={len(multiindex)} incompatible with the shelves (len={len(shelves)}).')

        shelves = [Rack.try_deserialize(s) for s in shelves]
        rack = cls()
        rack.multiindex = multiindex
        rack.shelves = shelves
        return rack

    def __repr__(self):
        return f'<{self.__class__.__name__}{str(self.shelves)}>'


class RackEncoder(json.JSONEncoder):
    """
    usage:
    json.dumps(rack, cls=RackEncoder)
    """

    def __init__(self, *args, **kawrgs):
        super().__init__(*args, **kawrgs)

    def default(self, obj: Any):
        if isinstance(obj, Rack):
            return obj.serializable
        super().default(obj)


class RackDecoder(json.JSONDecoder):
    """
    usage:
    json.loads(rack, cls=RackDecoder)
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def decode(self, obj: str):
        obj = super().decode(obj)
        obj = self.decode_dispatch(obj)
        return obj

    def decode_dispatch(self, obj):
        if (isinstance(obj, list) and
                len(obj) == 3 and
                obj[0] == 'Rack' and
                isinstance(obj[1], int) and
                isinstance(obj[2], list)):
            return Rack.deserialize(obj)
        elif isinstance(obj, list):
            return [self.decode_dispatch(member) for member in obj]
        elif isinstance(obj, Mapping):
            return {k: self.decode_dispatch(v) for k, v in obj.items()}
        else:
            return obj
