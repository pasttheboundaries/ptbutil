import os


class MultipleRead:
    """An iterable and iterator over multiple files.
    Methods:
        __iter__ : as per iterator protocol
        __next__ : as per iterator protocol
        readlines : returns a list of lines read from files
        readline : returns next line from files. This is practically an equivalent to next(self)
        """
    def __init__(self, filenames: list, mode: str = None, encoding: str = 'utf-8') -> None:
        """
        :param filenames: a list of files paths as strings.
        :param mode: str one of r, r+, rb
        :encoding: str -  default 'utf-8'
        """
        self.filenames = filenames
        self.mode = mode or 'r'
        self.encoding = encoding
        self._validate_filenames()
        self._validate_modes()
        self.current_iterator = self._get_current()
        self.current_filename = None
        self.current_file = None

    def _validate_filenames(self):
        for filename in self.filenames:
            if not os.path.isfile(filename):
                raise FileNotFoundError(f': {filename}')
        return True

    def _validate_modes(self):
        if self.mode not in ('r', 'r+', 'rb'):
            raise NotImplementedError(f'This class implements file reading only. Can not use mode {self.mode}')

    def _get_current(self):
        for filename in self.filenames:
            self.current_filename = filename
            with open(filename, self.mode, encoding=self.encoding) as f:
                self.current_file = f
                try:
                    yield f.readline()
                except StopIteration:
                    pass
        self.current_filename = None
        self.current_file = None

    def __enter__(self):
        return iter(self)

    def __exit__(self, er_name, er_tx, er_tb):
        return True

    def __iter__(self):
        self.current_iterator = self._get_current()
        return self

    def __next__(self):
        return next(self.current_iterator)

    def readlines(self) -> list:
        return [line for line in iter(self)]

    def readline(self):
        return next(self)
