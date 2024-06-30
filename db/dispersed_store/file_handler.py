import pandas as pd
from dataclasses import dataclass, field
from collections.abc import Hashable, Mapping
from typing import Any, Optional
from .errors import MaxSizeReached


@dataclass
class IndexedData:
    ind: Hashable = field(init=True, hash=True, repr=True)
    val: Any = field(init=True, default=None, repr=True)

    def __post_init__(self):
        if not isinstance(self.ind, Hashable):
            raise TypeError(f'Index must be hashable. Got type {type(self.ind)}')

    def to_dict(self):
        if isinstance(self.val, Mapping):
            val = self.val
        else:
            val = {'cont': self.val}
        return {self.ind: val}

    def to_dataframe(self):
        return pd.DataFrame(self.to_dict()).T


class FileHandler:
    """
        Filehandler workflow:

        fh = FileHandler(path)
        fh.open()  # this deliveres actual data structure read from the data
        fh.append(crawl_result)  # this appends to the data structure
        fh.dump() # this dumps the data structure to the data
        fh.close() # this purges data structure from memeory

        all methods return self
        so it is possible to write:
        FileHandler(path).open().append(crawl_result).dump().close()

        after:
        fh.open()
        the opened resource is accesible in data attribute:
        fh = FileHandler(path)
        fh.open()
        data = fh.data

        FileHandler are context managers
        with FileHandler(path) as f: #opens the csv
            f.append(crawl_result) # appends crawl_result
            # exiting the context performs: f.dump and f.close

        """
    def open(self):
        ...

    def append(self, data):
        ...

    def dump(self):
        ...

    def close(self):
        self.data = None

    def resources(self):
        """
        returns identifying values of the resources
        value in case of serial data
        index in case of indexed data
        """
        if not self.data:
            self.open()
        yield from self.data

    def __init__(self,
                 path,
                 max_size: Optional[int] = None):
        self.data = None
        self.path = path
        self.max_size = max_size

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.dump()
        self.close()

    def __contains__(self, item) -> bool:
        if not self.data:
            self.open()
        return item in self.resources


class CSVFileHandler(FileHandler):
    """
    DispersedIndexedStore existing_files can store only indexed data
    index and data must be passed to method append as a tuple or tuple like object
    data handlers facilitate the workflow below:
    fh = FileHandler(path)
    fh.open()
    indexed_data = IndexedData(2, 13)
    fh.append(indexed_data)
    fh.dump()
    fh.close()

    all methods return self
    so it is possible to write:
    FileHandler(path).open().append(crawl_result).dump().close()

    after:
    fh.open()
    the opened resource is accesible in data attribute:
    fh = FileHandler(path)
    fh.open()
    data = fh.data

    FileHandler are context managers
    with FileHandler(path) as f: #opens the csv
        f.append(crawl_result) # appends crawl_result
        # exiting the context performs: f.dump and f.close


    Appendable data.
    CSVfile handler accepts only a data that can be unpacked into 2 values
    the first one of which will be the index
    the other represents the stored value
    like:
    data = (1, 'one')
    CSVFilehandler().open().append(data)

    the first element (index) should be hashable
    the second (value) must be serializable
    If a dict type is passed as the second value,
    all keys will serve as column names and the values will be stored seprateli in the seprapte columns.

    """

    def open(self):
        try:
            self.data = pd.read_csv(self.path, index_col='ind')
        except FileNotFoundError:
            self.data = pd.DataFrame()
        return self

    def append(self, d: IndexedData):
        if len(self.data) > self.max_size:
            raise MaxSizeReached
        ind, content = d
        if isinstance(content, dict):
            self.data.loc[ind, list(content.keys())] = list(content.values())
        else:
            self.data.at[ind, 'content'] = content
        return self

    def dump(self):
        self.data = self.data.drop_duplicates()
        if not len(self.data) < 1:
            self.data.to_csv(self.path, index=True, index_label='ind')
        return self

    def resources(self):
        if not self.data:
            self.open()
        yield from self.data.index


class TextFileHandler(FileHandler):
    def open(self):
        try:
            with open(self.path, 'r', encoding='utf-8') as f:
                self.data = f.read().split('\n')
        except FileNotFoundError:
            self.data = []
        return self

    def append(self, d):
        if self.max_size and len(self.data) > self.max_size:
            raise MaxSizeReached
        self.data.append(d)
        return self

    def dump(self):
        if not len(self.data) < 1:
            saveable = '\n'.join(self.data)
            with open(self.path, 'w', encoding='utf-8') as f:
                f.write(saveable)
        return self
