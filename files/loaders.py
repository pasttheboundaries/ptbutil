import textract

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Union, Callable, Optional
from .functions import files_in_dir

class BaseLoader(ABC):
    def __init__(self, path: Union[str, Path]):
        self.path = Path(path).absolute()

    @abstractmethod
    def load(self):
        ...


class TextLoader(BaseLoader):

    def load(self):
        return textract.process(str(self.path)).decode()


class DirectoryTextLoader(BaseLoader):

    def __init__(self,
                 path: Union[str, Path],
                 condition: Optional[Callable] = None,
                 extension: Optional[str] = None):
        super().__init__(path=path)
        self.condition = condition
        self.extension = extension

    def load(self):
        files = files_in_dir(str(self.path))
        if self.condition:
            files = (f for f in files if self.condition(f))
        if self.extension:
            files = (f for f in files if f.endswith(self.extension))
        for f in files:
            yield TextLoader(f).load()




