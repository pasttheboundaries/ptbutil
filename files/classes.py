import os


class MultipleRead:
    """An iterable and iterator of lines over multiple existing_files.
    Methods:
        __iter__ : as per iterator protocol
        __next__ : as per iterator protocol
        readlines : returns a list of lines read from existing_files
        readline : returns next line from existing_files. This is practically an equivalent to next(self)
        """
    def __init__(self, filenames: list, encoding: str = 'utf-8') -> None:
        """
        :param filenames: a list of existing_files paths as strings.
        :param mode: str one of r, r+, rb
        :encoding: str -  default 'utf-8'
        """
        self.filenames = filenames
        self.encoding = encoding
        self._validate_filenames()
        self.current_iterator = self._get_line_iterator()
        self.current_filename = None
        self.current_file = None

    def _validate_filenames(self):
        for filename in self.filenames:
            if not os.path.isfile(filename):
                raise FileNotFoundError(f': {filename}')
        return True

    def _get_line_iterator(self):
        for filename in self.filenames:
            self.current_filename = filename
            with open(filename, 'r', encoding=self.encoding) as f:
                self.current_file = f
                for line in f.readlines():
                    yield line
        self.current_filename = None
        self.current_file = None

    def __enter__(self):
        return iter(self)

    def __exit__(self, er_name, er_tx, er_tb):
        return True

    def __iter__(self):
        self.current_iterator = self._get_line_iterator()
        return self

    def __next__(self):
        return next(self.current_iterator)

    def readlines(self) -> list:
        return (line for line in iter(self))

    def readline(self):
        return next(self)

    def read(self):
        return ''.join(self.readlines())
