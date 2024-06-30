
import os
import pathlib
from typing import Optional
from .types_ import ProprietaryDataType, IndexedData, SerialData
from .name_rotator import FileNamesRotator
from .file_handler import CSVFileHandler, TextFileHandler, FileHandler
from .errors import MaxSizeReached
from threading import Lock


class HashesCache(set):
    def __init__(self, iterable=()):
        super().__init__(iterable)
        self.loaded = False


class DomainStore:
    proprietary_data_type = ProprietaryDataType
    file_handler_class = FileHandler

    def __init__(self,
                 directory: str,
                 domain: str,
                 extension: str,
                 max_file_size: Optional[int] = None,
                 dump_after: int = 100
                 ):

        self.max_file_size = max_file_size or 100
        self.domain = domain
        self.filenames_rotator = FileNamesRotator(directory=directory,domain=domain, extension=extension)
        self.file_handler = self.file_handler_class(
            self.filenames_rotator.current(path=True),
            max_size=self.max_file_size
        )
        self.dump_after = dump_after
        self.cache = []
        self._hashes = HashesCache()
        self.dump_lock = Lock()
        self.access_lock = Lock()

    def append(self, data, dump=False):
        data = self.proprietary_data_type.preprocess_data(data)
        self.cache.append(data)
        self._cache_hash(data)
        if dump or len(self.cache) > self.dump_after:
            self.dump()

    def _cache_hash(self, data):
        self.hashes.add(hash(data))

    def dump(self):
        with self.dump_lock:
            while self.cache:
                dumped_all = self._dump_sized()
                if dumped_all: # cache empty
                    print('got True')
                    break
                else:  # cache still contains data to be saved -> must rotate and continue
                    print('got False')
                    self.filenames_rotator.rotate()
                    self.file_handler = self.file_handler_class(
                        self.filenames_rotator.current(path=True),
                        max_size=self.max_file_size
                    )
                    continue

    def _dump_sized(self):
        with self.file_handler.open() as file_handler:
            while self.cache:
                try:
                    data = self.cache.pop(0)
                    file_handler.append(data)
                except MaxSizeReached:
                    self.cache.append(data)
                    return False  # cache still contains data to be saved -> must rotate and continue
            return True  # cache empty

    def resources(self):
        """
        a generator delivering open domain existing_files
        """
        for filepath in self.filenames_rotator.existing_files(path=True):
            yield from self.file_handler_class(filepath).resources()

    @property
    def hashes(self):
        if not self._hashes.loaded:
            with self.access_lock:
                for hashable in self.resources():
                    hashed = hash(hashable)
                    self._hashes.add(hashed)
                self._hashes.loaded = True
        return self._hashes

    def __contains__(self, item):
        item = hash(item)
        return item in self.hashes


class SerialDomainStore(DomainStore):
    """
    manipulates existing_files
    append: appends (and writes) crawl_result to the last data
    if the max size is exceded creates new data

    __contain__ for membership check
    """
    proprietary_data_type = SerialData
    file_handler_class = TextFileHandler


class IndexedDomainStore(DomainStore):
    """
    manipulates existing_files
    append: appends (and writes) crawl_result to the last data
    if the max size is exceded creates new data

    __contain__ for membership check
    """
    proprietary_data_type = IndexedData
    file_handler_class = CSVFileHandler


class DispersedDataStore:
    """
    Fasade:
    append: distributes data into domain stores and appends to their cache
    dump : saves crawiling results by dumping into existing_files all domain_stores

    Instantiation parameters:
    directory: str - absolute path to the store directory
    max_file_size: int number of lines saved in the data - which represents the number of pieces of information
    dump_after: int - limit of appended data before it automatically gets dumped into data
    extension: str - store existing_files extension - this will overide the default extension of the store class.
    """

    proprietary_domain_store_type = IndexedDomainStore
    proprietary_file_extension = ''
    DEFAULT_DOMAIN = 'store'

    def __init__(self, directory,
                 max_file_size=20_000,
                 dump_after=100,
                 extension=None):
        if not os.path.isdir(directory):
            raise ValueError(f'no such directory: {directory}')
        self.directory = str(pathlib.Path(directory).absolute())
        self.domain_stores = dict()
        self.max_file_size = max_file_size
        self.dump_after = dump_after
        self.extension = extension or self.__class__.proprietary_file_extension

    def dump(self):
        """
        dumps all cache into existing_files store
        """
        for domain in self.domain_stores:
            self.domain_stores[domain].dump()

    def _get_domain_store(self, domain):
        """
        returns a domain store if in self.domain_stores
        if not, first opens one and adds to self.domain_stores
        """
        domain_store = self.domain_stores.get(domain)
        if not domain_store:
            self.domain_stores[domain] = self.proprietary_domain_store_type(
                directory=self.directory,
                domain=domain,
                extension=self.extension,
                max_file_size=self.max_file_size,
                dump_after=self.dump_after
            )
            domain_store = self.domain_stores[domain]
        return domain_store

    def append(self, data, domain=DEFAULT_DOMAIN, dump=False):
        """
        appends and writes into existing_files DispersedIndexedStore
        """
        domain_store = self._get_domain_store(domain)
        domain_store.append(data, dump=dump)

    def hash_known(self, data, domain) -> bool:
        """
        equivalent of __contains__ but only compares hashes of indexes:
        """
        domain_store = self._get_domain_store(domain)
        return hash(data) in domain_store.hashes

    @property
    def cache(self):
        if not self.domain_stores:
            return None
        cached = list()
        for donain_store in self.domain_stores.values():
            for v in donain_store.cache:
                cached.append(v)
        return cached

    @property
    def paths(self):
        """
        returns paths of all existing_files included in the store
        """
        files = [file for file in os.listdir(self.directory) if file.endswith(self.extension)]
        files = [os.path.join(self.directory, file) for file in files]
        files = [file for file in files if os.path.isfile(file)]
        files = sorted(files, reverse=True)
        return files

    def resources(self):
        for name, store in self.domain_stores.items():
            yield from store.resources()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.dump()


class DispersedSerialStore(DispersedDataStore):
    proprietary_domain_store_type = SerialDomainStore
    proprietary_file_extension = 'sdd'


class DispersedIndexedStore(DispersedDataStore):
    proprietary_domain_store_type = IndexedDomainStore
    proprietary_file_extension = 'idd'


