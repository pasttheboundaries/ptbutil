from collections import namedtuple
from collections.abc import Mapping
from typing import Protocol, Any


def preprocess_serial_data(data):
    try:
        return SerialData(data)
    except Exception as e:
        raise RuntimeError('Could not cast data to type str.') from e


def preprocess_indexed_data(data):
    if isinstance(data, Mapping):
        if len(data) != 1:
            raise TypeError('If Mapping is used as indexed data it must be of length = 1, eg.: {"index1": "value"}')
        return IndexedData(*list(dict(data).items()).pop())
    else:
        raise TypeError('indexed data must be either Mapping or Iterable')


class ProprietaryDataType(Protocol):
    @classmethod
    def preprocess_data(cls, data) -> Any:
        ...


class IndexedData(namedtuple('IndexedData', field_names='ind val'), ProprietaryDataType):
    def __hash__(self):
        return hash(self.ind)

    @classmethod
    def preprocess_data(cls, data):
        return preprocess_indexed_data(data)


class SerialData(str, ProprietaryDataType):
    def __hash__(self):
        return hash(str(self))

    @classmethod
    def preprocess_data(cls, data):
        return preprocess_serial_data(data)

